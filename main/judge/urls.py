from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('problems/', views.ProblemListView.as_view(), name='problem_list'),
    path('problems/<int:pk>/', views.problem_detail, name='problem_detail'),
    path('problems/<int:pk>/run-test/', views.run_custom_test, name='run_custom_test'),
    path('submissions/', views.SubmissionHistoryView.as_view(), name='submission_history'),
    path('submissions/<int:pk>/', views.SubmissionDetailView.as_view(), name='submission_detail'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('accounts/register/', views.register_view, name='register'),
]
