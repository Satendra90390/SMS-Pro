from django.urls import path
from . import views
from .chat_views import public_chat_api

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_institution, name='register'),
    path('role-select/', views.role_select, name='role_select'),
    path('profile/', views.profile_view, name='profile'),
    path('chat/', public_chat_api, name='public_chat_api'),
]
