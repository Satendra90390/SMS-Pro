from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from core.models import Institution, Student, Faculty, Parent
from django.db import transaction


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'accounts/landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def role_select(request):
    user = request.user
    if not request.session.pop('oauth_new', False):
        return redirect('core:dashboard')
    if request.method == 'POST':
        role = request.POST.get('role', '')
        if role in ['admin', 'faculty', 'student', 'parent']:
            user.role = role
            user.save()
            return redirect('core:dashboard')
        messages.error(request, 'Please select a valid role.')
    return render(request, 'accounts/role_select.html')


def register_institution(request):
    if request.method == 'POST':
        inst_name = request.POST.get('inst_name', '').strip()
        inst_type = request.POST.get('inst_type', 'College')
        inst_phone = request.POST.get('inst_phone', '').strip()
        inst_email = request.POST.get('inst_email', '').strip()
        inst_address = request.POST.get('inst_address', '').strip()
        admin_name = request.POST.get('admin_name', '').strip()
        admin_username = request.POST.get('admin_username', '').strip()
        admin_password = request.POST.get('admin_password', '')
        admin_confirm = request.POST.get('admin_confirm', '')

        errors = []
        if not inst_name:
            errors.append('Institution name is required.')
        if not inst_phone:
            errors.append('Phone is required.')
        if not admin_name:
            errors.append('Admin name is required.')
        if not admin_username:
            errors.append('Username is required.')
        if len(admin_password) < 6:
            errors.append('Password must be at least 6 characters.')
        if admin_password != admin_confirm:
            errors.append('Passwords do not match.')
        if User.objects.filter(username=admin_username).exists():
            errors.append('Username already taken.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accounts/register.html')

        slug = inst_name.lower().replace(' ', '-').strip('-')
        import re
        slug = re.sub(r'[^\w\-]', '', slug)

        if Institution.objects.filter(slug=slug).exists():
            messages.error(request, 'An institution with this name already exists.')
            return render(request, 'accounts/register.html')

        inst = Institution.objects.create(
            name=inst_name, slug=slug, inst_type=inst_type,
            phone=inst_phone, email=inst_email, address=inst_address,
        )
        User.objects.create_user(
            username=admin_username, password=admin_password,
            role='admin', institution=inst, first_name=admin_name,
        )
        messages.success(request, 'Institution registered! You can now log in.')
        return redirect('accounts:login')
    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    user = request.user
    profile_data = None
    if hasattr(user, 'student_profile'):
        profile_data = user.student_profile
    elif hasattr(user, 'faculty_profile'):
        profile_data = user.faculty_profile
    elif hasattr(user, 'parent_profile'):
        profile_data = user.parent_profile

    if request.method == 'POST':
        confirm = request.POST.get('confirm_username', '')
        if confirm != user.username:
            messages.error(request, 'Username does not match. Account was not deleted.')
            return redirect('accounts:profile')
        with transaction.atomic():
            Student.objects.filter(user=user).update(user=None)
            Faculty.objects.filter(user=user).update(user=None)
            Parent.objects.filter(user=user).update(user=None)
            user.delete()
        logout(request)
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('accounts:landing')

    return render(request, 'accounts/profile.html', {'profile_data': profile_data})
