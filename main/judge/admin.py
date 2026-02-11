from django.contrib import admin
from .models import Problem, TestCase, Submission


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'time_limit', 'created_at')
    list_filter = ('difficulty',)
    search_fields = ('title',)
    inlines = [TestCaseInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'language', 'status', 'created_at')
    list_filter = ('status', 'language')
    search_fields = ('user__username', 'problem__title')
    readonly_fields = ('user', 'problem', 'code', 'language', 'status', 'output', 'created_at')
