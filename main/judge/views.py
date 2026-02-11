from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.http import Http404

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
