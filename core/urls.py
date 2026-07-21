from django.urls import path
from . import views
from .chat_views import chat_api

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_router, name='dashboard'),
    path('chat/', chat_api, name='chat_api'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', views.admin_students, name='admin_students'),
    path('admin/students/add/', views.admin_add_student, name='admin_add_student'),
    path('admin/faculty/', views.admin_faculty, name='admin_faculty'),
    path('admin/faculty/add/', views.admin_add_faculty, name='admin_add_faculty'),
    path('admin/subjects/', views.admin_subjects, name='admin_subjects'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/fees/', views.admin_fees, name='admin_fees'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('accountant/', views.accountant_dashboard, name='accountant_dashboard'),
    path('accountant/fees/', views.accountant_fees, name='accountant_fees'),
    path('accountant/fees/add/', views.accountant_add_fee, name='accountant_add_fee'),
    path('accountant/fees/<int:fee_id>/edit/', views.accountant_edit_fee, name='accountant_edit_fee'),
    path('accountant/collections/', views.accountant_collections, name='accountant_collections'),
    path('faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('parent/', views.parent_dashboard, name='parent_dashboard'),
]
