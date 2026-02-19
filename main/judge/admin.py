from django.contrib import admin
from .models import Problem, TestCase, Submission, Tag, TestCaseResult


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


class TestCaseResultInline(admin.TabularInline):
    model = TestCaseResult
    extra = 0
    readonly_fields = ('test_case', 'test_case_number', 'status', 'actual_output', 'execution_time', 'memory_used')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'time_limit', 'memory_limit', 'created_at')
    list_filter = ('difficulty', 'tags')
    search_fields = ('title',)
    filter_horizontal = ('tags',)
    inlines = [TestCaseInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'difficulty', 'tags'),
        }),
        ('Limits', {
            'fields': ('time_limit', 'memory_limit'),
        }),
        ('Editorial', {
            'fields': ('editorial',),
            'classes': ('collapse',),
        }),
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'language', 'status', 'created_at')
    list_filter = ('status', 'language')
    search_fields = ('user__username', 'problem__title')
    readonly_fields = ('user', 'problem', 'code', 'language', 'status', 'output', 'created_at')
    inlines = [TestCaseResultInline]
