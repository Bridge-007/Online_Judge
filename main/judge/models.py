from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Tag(models.Model):
    """Topic tag for categorising problems (e.g. Arrays, DP, Graphs)."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Full problem statement.")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='Easy')
    time_limit = models.FloatField(default=2.0, help_text="Time limit in seconds.")
    memory_limit = models.IntegerField(default=256, help_text="Memory limit in MB.")
    tags = models.ManyToManyField(Tag, blank=True, related_name='problems')
    editorial = models.TextField(blank=True, help_text="Solution explanation shown after AC.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField(blank=True, help_text="Input fed to stdin.")
    expected_output = models.TextField(help_text="Expected stdout output.")
    is_sample = models.BooleanField(default=False, help_text="If True, shown to the user on the problem page.")

    def __str__(self):
        return f"TestCase for {self.problem.title} (sample={self.is_sample})"


class Submission(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('cpp', 'C++'),
        ('java', 'Java'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Runtime Error', 'Runtime Error'),
        ('Compilation Error', 'Compilation Error'),
        ('Memory Limit Exceeded', 'Memory Limit Exceeded'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Pending')
    output = models.TextField(blank=True, null=True, help_text="Captured stdout/stderr or error message.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.problem.title} — {self.status}"


class TestCaseResult(models.Model):
    """Per-test-case verdict for a submission."""
    STATUS_CHOICES = [
        ('Passed', 'Passed'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Runtime Error', 'Runtime Error'),
        ('Memory Limit Exceeded', 'Memory Limit Exceeded'),
    ]

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='test_case_results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    test_case_number = models.IntegerField(default=0)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES)
    actual_output = models.TextField(blank=True)
    execution_time = models.FloatField(null=True, blank=True, help_text="Time in seconds.")
    memory_used = models.FloatField(null=True, blank=True, help_text="Peak memory in MB.")

    class Meta:
        ordering = ['test_case_number']

    def __str__(self):
        return f"TC#{self.test_case_number} — {self.status}"
