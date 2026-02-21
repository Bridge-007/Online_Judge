from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Problem, Submission, Tag
from .forms import RegistrationForm, SubmissionForm
from .engine import judge_submission, LANGUAGE_CONFIG


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
def home(request):
    """Landing page with conditional login/register vs dashboard links."""
    return render(request, 'home.html')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
def register_view(request):
    """User registration using RegistrationForm."""
    if request.user.is_authenticated:
        return redirect('problem_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


# ---------------------------------------------------------------------------
# Problem List (Dashboard) — with Search & Filtering
# ---------------------------------------------------------------------------
class ProblemListView(ListView):
    model = Problem
    template_name = 'judge/problem_list.html'
    context_object_name = 'problems'

    def get_queryset(self):
        qs = Problem.objects.prefetch_related('tags').all()

        # --- Search by title ---
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(title__icontains=q)

        # --- Filter by difficulty ---
        difficulty = self.request.GET.get('difficulty', '').strip()
        if difficulty in ('Easy', 'Medium', 'Hard'):
            qs = qs.filter(difficulty=difficulty)

        # --- Filter by tag ---
        tag_slug = self.request.GET.get('tag', '').strip()
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        # --- Filter by solved / unsolved ---
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter and self.request.user.is_authenticated:
            solved_ids = set(
                Submission.objects.filter(
                    user=self.request.user,
                    status='Accepted',
                ).values_list('problem_id', flat=True)
            )
            if status_filter == 'solved':
                qs = qs.filter(pk__in=solved_ids)
            elif status_filter == 'unsolved':
                qs = qs.exclude(pk__in=solved_ids)

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Solved IDs for status badges
        if self.request.user.is_authenticated:
            solved_ids = set(
                Submission.objects.filter(
                    user=self.request.user,
                    status='Accepted',
                ).values_list('problem_id', flat=True)
            )
        else:
            solved_ids = set()
        context['solved_ids'] = solved_ids

        # All tags for the filter dropdown
        context['all_tags'] = Tag.objects.all()

        # Preserve current filter values in the template
        context['current_q'] = self.request.GET.get('q', '')
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['current_tag'] = self.request.GET.get('tag', '')
        context['current_status'] = self.request.GET.get('status', '')

        return context


# ---------------------------------------------------------------------------
# Problem Detail & Submit
# ---------------------------------------------------------------------------
@login_required
def problem_detail(request, pk):
    """Show problem details + sample test cases; handle code submission."""
    problem = get_object_or_404(Problem.objects.prefetch_related('tags'), pk=pk)
    sample_cases = problem.test_cases.filter(is_sample=True)

    # Check if the user has solved this problem (for editorial visibility)
    has_solved = Submission.objects.filter(
        user=request.user,
        problem=problem,
        status='Accepted',
    ).exists()

    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.problem = problem
            submission.status = 'Pending'
            submission.save()

            # Run the judge engine synchronously
            judge_submission(submission)

            return redirect('submission_detail', pk=submission.pk)
    else:
        form = SubmissionForm()

    return render(request, 'judge/problem_detail.html', {
        'problem': problem,
        'sample_cases': sample_cases,
        'form': form,
        'has_solved': has_solved,
    })


# ---------------------------------------------------------------------------
# Run Custom Test Case (AJAX)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def run_custom_test(request, pk):
    """Run user code against a single custom input (no Submission created)."""
    import os, sys, subprocess, tempfile, shutil

    problem = get_object_or_404(Problem, pk=pk)
    code = request.POST.get('code', '')
    language = request.POST.get('language', '')
    custom_input = request.POST.get('custom_input', '')

    config = LANGUAGE_CONFIG.get(language)
    if config is None:
        return JsonResponse({'error': f'Unsupported language: {language}'})

    if not code.strip():
        return JsonResponse({'error': 'No code provided.'})

    sandbox = tempfile.mkdtemp(prefix='oj_custom_')
    try:
        # Write code
        code_path = os.path.join(sandbox, config['filename'])
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # Compile if needed
        if config['compile'] is not None:
            compile_cmd = config['compile'](sandbox)
            try:
                result = subprocess.run(
                    compile_cmd, capture_output=True, text=True, timeout=30,
                )
                if result.returncode != 0:
                    return JsonResponse({'error': 'Compilation Error', 'output': result.stderr[:2000]})
            except FileNotFoundError:
                return JsonResponse({'error': f'Compiler not found for {language}.'})

        # Run
        run_cmd = config['run'](sandbox)
        try:
            result = subprocess.run(
                run_cmd,
                input=custom_input,
                capture_output=True,
                text=True,
                timeout=problem.time_limit,
            )
        except subprocess.TimeoutExpired:
            return JsonResponse({'error': 'Time Limit Exceeded'})

        if result.returncode != 0:
            error_msg = result.stderr[:2000] if result.stderr else 'Non-zero exit code.'
            return JsonResponse({'error': 'Runtime Error', 'output': error_msg})

        return JsonResponse({'output': result.stdout})
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ---------------------------------------------------------------------------
# Submission Detail (Result) — with Per-Test-Case Verdicts
# ---------------------------------------------------------------------------
class SubmissionDetailView(LoginRequiredMixin, DetailView):
    model = Submission
    template_name = 'judge/submission_detail.html'
    context_object_name = 'submission'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Access control: only the submission owner can view it
        if obj.user != self.request.user:
            raise Http404("You do not have permission to view this submission.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test_case_results'] = self.object.test_case_results.all()
        return context


# ---------------------------------------------------------------------------
# AI Code Review
# ---------------------------------------------------------------------------
@login_required
@require_POST
def ai_review(request, pk):
    """Generate an AI review of the user's submitted code."""
    import json
    import urllib.request
    import urllib.error

    submission = get_object_or_404(Submission, pk=pk)
    if submission.user != request.user:
        return JsonResponse({'error': 'Access denied.'}, status=403)

    from django.conf import settings
    api_key = getattr(settings, 'HUGGINGFACE_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'AI review is not configured.'}, status=500)

    # Build the prompt
    problem = submission.problem
    language_display = submission.get_language_display()
    prompt = (
        f"You are an expert code reviewer for a competitive programming platform.\n"
        f"Review the following {language_display} solution and provide concise, actionable feedback.\n\n"
        f"## Problem: {problem.title}\n"
        f"Difficulty: {problem.difficulty}\n\n"
        f"### Problem Statement:\n{problem.description}\n\n"
        f"### Submitted Code ({language_display}):\n```\n{submission.code}\n```\n\n"
        f"### Verdict: {submission.status}\n\n"
        f"Please provide:\n"
        f"1. **Code Quality**: Style, readability, naming conventions\n"
        f"2. **Correctness**: Any logical bugs or edge cases missed\n"
        f"3. **Efficiency**: Time/space complexity analysis and potential optimizations\n"
        f"4. **Suggestions**: Concrete improvements with brief explanations\n\n"
        f"Keep your review concise and helpful. Use markdown formatting."
    )

    payload = json.dumps({
        'model': 'Qwen/Qwen2.5-Coder-32B-Instruct',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 1024,
        'temperature': 0.7,
    }).encode()

    req = urllib.request.Request(
        'https://router.huggingface.co/v1/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read().decode())
        review_text = result['choices'][0]['message']['content']
        return JsonResponse({'review': review_text})
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        return JsonResponse({'error': f'AI service error ({e.code}): {body}'}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Failed to get AI review: {str(e)}'}, status=500)


# ---------------------------------------------------------------------------
# Submission History
# ---------------------------------------------------------------------------
class SubmissionHistoryView(LoginRequiredMixin, ListView):
    model = Submission
    template_name = 'judge/submission_list.html'
    context_object_name = 'submissions'

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# User Profile
# ---------------------------------------------------------------------------
@login_required
def profile_view(request, username):
    """User profile page with comprehensive submission statistics."""
    profile_user = get_object_or_404(User, username=username)
    submissions = Submission.objects.filter(user=profile_user)

    # --- Core counts ---
    total_submissions = submissions.count()
    problems_attempted = submissions.values('problem').distinct().count()
    solved_problem_ids = set(
        submissions.filter(status='Accepted')
        .values_list('problem_id', flat=True)
        .distinct()
    )
    problems_solved = len(solved_problem_ids)
    accuracy = round((problems_solved / problems_attempted) * 100, 1) if problems_attempted else 0

    # --- Current streak (consecutive days ending today with ≥1 Accepted) ---
    streak = 0
    today = timezone.now().date()
    accepted_dates = set(
        submissions.filter(status='Accepted')
        .values_list('created_at__date', flat=True)
        .distinct()
    )
    check_date = today
    while check_date in accepted_dates:
        streak += 1
        check_date -= timedelta(days=1)

    # --- Verdict breakdown ---
    verdict_counts = dict(
        submissions.values_list('status')
        .annotate(count=Count('id'))
        .values_list('status', 'count')
    )

    # --- Language breakdown ---
    language_counts = dict(
        submissions.values_list('language')
        .annotate(count=Count('id'))
        .values_list('language', 'count')
    )

    # --- Difficulty breakdown (solved problems only) ---
    difficulty_counts = {}
    if solved_problem_ids:
        difficulty_counts = dict(
            Problem.objects.filter(id__in=solved_problem_ids)
            .values_list('difficulty')
            .annotate(count=Count('id'))
            .values_list('difficulty', 'count')
        )

    # --- Recent submissions ---
    recent_submissions = submissions.select_related('problem')[:10]

    context = {
        'profile_user': profile_user,
        'total_submissions': total_submissions,
        'problems_attempted': problems_attempted,
        'problems_solved': problems_solved,
        'accuracy': accuracy,
        'streak': streak,
        'verdict_counts': verdict_counts,
        'language_counts': language_counts,
        'difficulty_counts': difficulty_counts,
        'recent_submissions': recent_submissions,
    }
    return render(request, 'judge/profile.html', context)
