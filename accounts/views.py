from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from sms_django.turnstile import verify_turnstile
from .models import User
from core.models import Institution, Student, Faculty, Parent
from django.db import transaction
from django.http import JsonResponse


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if not request.session.get('turnstile_verified'):
        return redirect('accounts:verify')
    return render(request, 'accounts/landing.html')


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def verify_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.session.get('turnstile_verified'):
        return redirect('accounts:landing')
    if request.method == 'POST':
        token = request.POST.get('cf-turnstile-response', '')
        if verify_turnstile(token, request.META.get('REMOTE_ADDR')):
            request.session['turnstile_verified'] = True
            return redirect('accounts:landing')
        messages.error(request, 'Verification failed. Please try again.')
    return render(request, 'accounts/verify.html')


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        token = request.POST.get('cf-turnstile-response', '')
        if not verify_turnstile(token, request.META.get('REMOTE_ADDR')):
            messages.error(request, 'Human verification failed. Please try again.')
            return render(request, 'accounts/login.html')
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
    if request.method == 'POST':
        logout(request)
    return redirect('accounts:login')


@login_required
def role_select(request):
    user = request.user
    if not request.session.pop('oauth_new', False):
        return redirect('core:dashboard')

    step = request.session.get('role_select_step', '1')
    inst_id = request.session.get('role_select_inst_id')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'verify_code':
            invite_code = request.POST.get('invite_code', '').strip().upper()
            if not invite_code:
                messages.error(request, 'Please enter the invite code from your admin.')
                return render(request, 'accounts/role_select.html', {'step': '1'})
            try:
                institution = Institution.objects.get(invite_code=invite_code, is_active=True)
            except Institution.DoesNotExist:
                messages.error(request, 'Invalid invite code. Please check with your admin.')
                return render(request, 'accounts/role_select.html', {'step': '1'})
            request.session['role_select_step'] = '2'
            request.session['role_select_inst_id'] = institution.id
            return render(request, 'accounts/role_select.html', {
                'step': '2', 'institution': institution,
            })

        if action == 'pick_role':
            role = request.POST.get('role', '').strip()
            if role == 'admin':
                request.session.pop('role_select_step', None)
                request.session.pop('role_select_inst_id', None)
                return redirect('accounts:register')

            if role not in ['accountant', 'faculty', 'student', 'parent', 'librarian']:
                messages.error(request, 'Please select a valid role.')
                institution = get_object_or_404(Institution, pk=inst_id)
                return render(request, 'accounts/role_select.html', {
                    'step': '2', 'institution': institution,
                })

            institution = get_object_or_404(Institution, pk=inst_id)
            user.role = role
            user.institution = institution
            user.save()

            if role == 'student':
                Student.objects.get_or_create(user=user, institution=institution, defaults={'name': user.get_full_name() or user.username, 'age': 18, 'sex': 'Other', 'phone': user.phone or ''})
            elif role == 'faculty':
                Faculty.objects.get_or_create(user=user, institution=institution, defaults={'name': user.get_full_name() or user.username, 'department': '', 'phone': user.phone or '', 'qualification': ''})

            request.session.pop('role_select_step', None)
            request.session.pop('role_select_inst_id', None)
            messages.success(request, f'Welcome! You are registered as {role.title()} at {institution.name}.')
            return redirect('core:dashboard')

        if action == 'back':
            request.session['role_select_step'] = '1'
            request.session.pop('role_select_inst_id', None)
            return render(request, 'accounts/role_select.html', {'step': '1'})

    if step == '2' and inst_id:
        institution = get_object_or_404(Institution, pk=inst_id)
        return render(request, 'accounts/role_select.html', {
            'step': '2', 'institution': institution,
        })

    return render(request, 'accounts/role_select.html', {'step': '1'})


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def register_institution(request):
    if request.method == 'POST':
        token = request.POST.get('cf-turnstile-response', '')
        if not verify_turnstile(token, request.META.get('REMOTE_ADDR')):
            messages.error(request, 'Human verification failed. Please try again.')
            return render(request, 'accounts/register.html')
        inst_name = request.POST.get('inst_name', '').strip()
        inst_type = request.POST.get('inst_type', 'College')
        inst_phone = request.POST.get('inst_phone', '').strip()
        inst_email = request.POST.get('inst_email', '').strip()
        inst_address = request.POST.get('inst_address', '').strip()
        admin_name = request.POST.get('admin_name', '').strip()
        admin_username = request.POST.get('admin_username', '').strip()
        admin_password = request.POST.get('admin_password', '')
        admin_confirm = request.POST.get('admin_confirm', '')

        form_data = {
            'inst_name': inst_name, 'inst_type': inst_type,
            'inst_phone': inst_phone, 'inst_email': inst_email,
            'inst_address': inst_address, 'admin_name': admin_name,
            'admin_username': admin_username,
        }

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
        if admin_username and User.objects.filter(username=admin_username).exists():
            errors.append('Username already taken.')

        if errors:
            for e in errors:
                messages.error(request, e)
            form_data['step2'] = True
            return render(request, 'accounts/register.html', form_data)

        slug = inst_name.lower().replace(' ', '-').strip('-')
        import re
        slug = re.sub(r'[^\w\-]', '', slug)

        if Institution.objects.filter(slug=slug).exists():
            messages.error(request, 'An institution with this name already exists.')
            form_data['step2'] = True
            return render(request, 'accounts/register.html', form_data)

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


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def self_register(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        step = request.POST.get('step', '1')
        invite_code = request.POST.get('invite_code', '').strip().upper()
        inst_id = request.POST.get('inst_id', '')
        role = request.POST.get('role', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        phone = request.POST.get('phone', '').strip()

        if step == '1':
            if not invite_code:
                messages.error(request, 'Please enter an invite code.')
                return render(request, 'accounts/self_register.html', {'step': '1'})
            try:
                institution = Institution.objects.get(invite_code=invite_code, is_active=True)
            except Institution.DoesNotExist:
                messages.error(request, 'Invalid invite code. Please check with your institution.')
                return render(request, 'accounts/self_register.html', {'step': '1'})
            return render(request, 'accounts/self_register.html', {
                'step': '2', 'institution': institution,
                'inst_id': institution.id, 'invite_code': invite_code,
            })

        elif step == '2':
            try:
                institution = Institution.objects.get(pk=inst_id, is_active=True)
            except Institution.DoesNotExist:
                messages.error(request, 'Institution not found.')
                return render(request, 'accounts/self_register.html', {'step': '1'})
            if role not in ['student', 'faculty', 'parent', 'accountant', 'librarian']:
                messages.error(request, 'Please select a valid role.')
                return render(request, 'accounts/self_register.html', {
                    'step': '2', 'institution': institution,
                    'inst_id': inst_id, 'invite_code': invite_code,
                })
            return render(request, 'accounts/self_register.html', {
                'step': '3', 'institution': institution,
                'inst_id': inst_id, 'invite_code': invite_code,
                'role': role,
            })

        elif step == '3':
            token = request.POST.get('cf-turnstile-response', '')
            if not verify_turnstile(token, request.META.get('REMOTE_ADDR')):
                messages.error(request, 'Human verification failed. Please try again.')
                return render(request, 'accounts/self_register.html', {
                    'step': '3', 'institution': institution,
                    'inst_id': inst_id, 'invite_code': invite_code,
                    'role': role, 'full_name': full_name,
                    'username': username, 'phone': phone,
                })
            try:
                institution = Institution.objects.get(pk=inst_id, is_active=True)
            except Institution.DoesNotExist:
                messages.error(request, 'Institution not found.')
                return render(request, 'accounts/self_register.html', {'step': '1'})
            if role not in ['student', 'faculty', 'parent', 'accountant', 'librarian']:
                messages.error(request, 'Invalid role.')
                return redirect('accounts:self_register')
            if not full_name:
                messages.error(request, 'Full name is required.')
                return render(request, 'accounts/self_register.html', {
                    'step': '3', 'institution': institution,
                    'inst_id': inst_id, 'invite_code': invite_code,
                    'role': role, 'full_name': full_name,
                    'username': username, 'phone': phone,
                })
            if not username:
                messages.error(request, 'Username is required.')
                return render(request, 'accounts/self_register.html', {
                    'step': '3', 'institution': institution,
                    'inst_id': inst_id, 'invite_code': invite_code,
                    'role': role, 'full_name': full_name,
                    'username': username, 'phone': phone,
                })
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
                return render(request, 'accounts/self_register.html', {
                    'step': '3', 'institution': institution,
                    'inst_id': inst_id, 'invite_code': invite_code,
                    'role': role, 'full_name': full_name,
                    'username': username, 'phone': phone,
                })
            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
                return render(request, 'accounts/self_register.html', {
                    'step': '3', 'institution': institution,
                    'inst_id': inst_id, 'invite_code': invite_code,
                    'role': role, 'full_name': full_name,
                    'username': username, 'phone': phone,
                })
            if password != confirm:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/self_register.html', {
                    'step': '3', 'institution': institution,
                    'inst_id': inst_id, 'invite_code': invite_code,
                    'role': role, 'full_name': full_name,
                    'username': username, 'phone': phone,
                })

            user = User.objects.create_user(
                username=username, password=password,
                role=role, institution=institution, first_name=full_name,
                phone=phone,
            )

            if role == 'student':
                age = request.POST.get('age', 18)
                sex = request.POST.get('sex', 'Male')
                Student.objects.create(
                    institution=institution, user=user,
                    name=full_name, age=int(age) if age else 18,
                    sex=sex, phone=phone,
                )
            elif role == 'faculty':
                department = request.POST.get('department', '').strip()
                qualification = request.POST.get('qualification', '').strip()
                email = request.POST.get('email', '').strip()
                Faculty.objects.create(
                    institution=institution, user=user,
                    name=full_name, department=department,
                    phone=phone, qualification=qualification, email=email,
                )
            elif role == 'parent':
                email = request.POST.get('email', '').strip()
                relationship = request.POST.get('relationship', '').strip()
                child_name = request.POST.get('child_name', '').strip()
                child = None
                if child_name:
                    child = Student.objects.filter(
                        institution=institution, name__icontains=child_name
                    ).first()
                if child:
                    Parent.objects.create(
                        institution=institution, user=user,
                        name=full_name, phone=phone, email=email,
                        relationship=relationship, child=child,
                    )

            login(request, user)
            messages.success(request, f'Welcome to {institution.name}, {full_name}!')
            return redirect('core:dashboard')

    return render(request, 'accounts/self_register.html', {'step': '1'})
