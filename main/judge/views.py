from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Problem, Submission
from .forms import RegistrationForm, SubmissionForm
from .engine import judge_submission


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
# Problem List (Dashboard)
# ---------------------------------------------------------------------------
class ProblemListView(LoginRequiredMixin, ListView):
    model = Problem
    template_name = 'judge/problem_list.html'
    context_object_name = 'problems'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Collect set of problem IDs the current user has solved (Accepted)
        solved_ids = set(
            Submission.objects.filter(
                user=self.request.user,
                status='Accepted',
            ).values_list('problem_id', flat=True)
        )
        context['solved_ids'] = solved_ids
        return context


# ---------------------------------------------------------------------------
# Problem Detail & Submit
# ---------------------------------------------------------------------------
@login_required
def problem_detail(request, pk):
    """Show problem details + sample test cases; handle code submission."""
    problem = get_object_or_404(Problem, pk=pk)
    sample_cases = problem.test_cases.filter(is_sample=True)

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
    })


# ---------------------------------------------------------------------------
# Submission Detail (Result)
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
