from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('problems/', views.ProblemListView.as_view(), name='problem_list'),
    path('problems/<int:pk>/', views.problem_detail, name='problem_detail'),
    path('submissions/', views.SubmissionHistoryView.as_view(), name='submission_history'),
    path('submissions/<int:pk>/', views.SubmissionDetailView.as_view(), name='submission_detail'),
    path('accounts/register/', views.register_view, name='register'),
]
