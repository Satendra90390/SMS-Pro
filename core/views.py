from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from datetime import date, timedelta
from .models import (
    Institution, Student, Faculty, Course, FacultyTeaching,
    StudentCourse, Result, Attendance, Fee, Parent, AuditLog,
)
from accounts.models import User


def log_audit(user, action, details="", collection=""):
    AuditLog.objects.create(
        institution=user.institution, action=action,
        username=user.username, role=user.role,
        details=details, collection=collection,
    )


def dashboard_router(request):
    role = request.user.role
    if role == 'admin':
        return redirect('core:admin_dashboard')
    elif role == 'faculty':
        return redirect('core:faculty_dashboard')
    elif role == 'student':
        return redirect('core:student_dashboard')
    elif role == 'parent':
        return redirect('core:parent_dashboard')
    return redirect('accounts:login')


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    ctx = {
        'student_count': Student.objects.filter(institution=inst).count(),
        'faculty_count': Faculty.objects.filter(institution=inst).count(),
        'total_attendance': Attendance.objects.filter(institution=inst).count(),
        'present_count': Attendance.objects.filter(institution=inst, status='Present').count(),
        'absent_count': Attendance.objects.filter(institution=inst, status='Absent').count(),
        'fees_collected': Fee.objects.filter(institution=inst, status='Paid').aggregate(total=Sum('amount'))['total'] or 0,
        'total_fees': Fee.objects.filter(institution=inst).values('status').annotate(total=Sum('amount')),
        'institution': inst,
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


@login_required
def admin_students(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    students = Student.objects.filter(institution=inst).order_by('name')
    q = request.GET.get('q', '').strip()
    if q:
        students = students.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    if request.method == 'POST' and request.POST.get('delete_id'):
        sid = request.POST.get('delete_id')
        try:
            s = Student.objects.get(pk=sid, institution=inst)
            name = s.name
            s.delete()
            log_audit(request.user, 'delete_student', f"Deleted student {name}", 'student_details')
            messages.success(request, f'Student "{name}" deleted.')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
        return redirect('core:admin_students')
    return render(request, 'admin_panel/students.html', {'students': students})


@login_required
def admin_add_student(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        age = request.POST.get('age', 18)
        sex = request.POST.get('sex', 'Male')
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        errors = []
        if not name:
            errors.append('Name is required.')
        if not phone:
            errors.append('Phone is required.')
        if not username:
            errors.append('Username is required.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'admin_panel/add_student.html')

        user = User.objects.create_user(
            username=username, password=password,
            role='student', institution=inst,
        )
        student = Student.objects.create(
            institution=inst, user=user, name=name,
            age=int(age), sex=sex, phone=phone,
        )
        log_audit(request.user, 'add_student', f"Added student {name}", 'student_details')
        messages.success(request, f'Student "{name}" added successfully.')
        return redirect('core:admin_students')
    return render(request, 'admin_panel/add_student.html')


@login_required
def admin_faculty(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    faculty_list = Faculty.objects.filter(institution=inst).order_by('name')
    return render(request, 'admin_panel/faculty.html', {'faculty_list': faculty_list})


@login_required
def admin_add_faculty(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        department = request.POST.get('department', '').strip()
        phone = request.POST.get('phone', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'admin_panel/add_faculty.html')

        user = User.objects.create_user(
            username=username, password=password,
            role='faculty', institution=inst,
        )
        Faculty.objects.create(
            institution=inst, user=user, name=name,
            department=department, phone=phone,
            qualification=qualification, email=email,
        )
        log_audit(request.user, 'add_faculty', f"Added faculty {name}", 'faculty_details')
        messages.success(request, f'Faculty "{name}" added successfully.')
        return redirect('core:admin_faculty')
    return render(request, 'admin_panel/add_faculty.html')


@login_required
def admin_subjects(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    courses = Course.objects.filter(institution=inst)
    teachings = FacultyTeaching.objects.filter(institution=inst).select_related('faculty', 'course')
    return render(request, 'admin_panel/subjects.html', {'courses': courses, 'teachings': teachings})


@login_required
def admin_reports(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    results = Result.objects.filter(institution=inst).select_related('student', 'faculty', 'course')[:100]
    return render(request, 'admin_panel/reports.html', {'results': results})


@login_required
def admin_fees(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    fees = Fee.objects.filter(institution=inst).select_related('student')
    total_collected = fees.filter(status='Paid').aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'admin_panel/fees.html', {
        'fees': fees, 'total_collected': total_collected,
    })


@login_required
def admin_analytics(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    total = Attendance.objects.filter(institution=inst).count()
    present = Attendance.objects.filter(institution=inst, status='Present').count() if total else 0
    absent = Attendance.objects.filter(institution=inst, status='Absent').count() if total else 0
    ctx = {
        'student_count': Student.objects.filter(institution=inst).count(),
        'faculty_count': Faculty.objects.filter(institution=inst).count(),
        'course_count': Course.objects.filter(institution=inst).count(),
        'attendance_rate': round(present / total * 100, 1) if total else 0,
        'present_count': present,
        'absent_count': absent,
    }
    return render(request, 'admin_panel/analytics.html', ctx)


@login_required
def faculty_dashboard(request):
    if request.user.role != 'faculty':
        return redirect('core:dashboard')
    inst = request.user.institution
    try:
        faculty_obj = Faculty.objects.get(user=request.user, institution=inst)
    except Faculty.DoesNotExist:
        faculty_obj = None
    teachings = FacultyTeaching.objects.filter(faculty=faculty_obj, institution=inst) if faculty_obj else []
    return render(request, 'faculty/dashboard.html', {
        'faculty_obj': faculty_obj, 'teachings': teachings,
    })


@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('core:dashboard')
    inst = request.user.institution
    try:
        student_obj = Student.objects.get(user=request.user, institution=inst)
    except Student.DoesNotExist:
        student_obj = None
    results = Result.objects.filter(student=student_obj, institution=inst) if student_obj else []
    fees = Fee.objects.filter(student=student_obj, institution=inst) if student_obj else []
    return render(request, 'student/dashboard.html', {
        'student_obj': student_obj, 'results': results, 'fees': fees,
    })


@login_required
def parent_dashboard(request):
    if request.user.role != 'parent':
        return redirect('core:dashboard')
    inst = request.user.institution
    try:
        parent_obj = Parent.objects.get(user=request.user, institution=inst)
    except Parent.DoesNotExist:
        parent_obj = None
    return render(request, 'parent/dashboard.html', {'parent_obj': parent_obj})
