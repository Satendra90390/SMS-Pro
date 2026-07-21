from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from datetime import date, timedelta
from .models import (
    Institution, Student, Faculty, Course, FacultyTeaching,
    StudentCourse, Result, Attendance, Fee, Parent, AuditLog,
    Exam, ExamResult, Book, BookIssue, Event,
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
    elif role == 'accountant':
        return redirect('core:accountant_dashboard')
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
        'exam_count': Exam.objects.filter(institution=inst).count(),
        'book_count': Book.objects.filter(institution=inst).count(),
        'event_count': Event.objects.filter(institution=inst).count(),
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


@login_required
def accountant_dashboard(request):
    if request.user.role != 'accountant':
        return redirect('core:dashboard')
    inst = request.user.institution
    fees = Fee.objects.filter(institution=inst)
    total_collected = fees.filter(status='Paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = fees.filter(status='Pending').aggregate(total=Sum('amount'))['total'] or 0
    total_partial = fees.filter(status='Partial').aggregate(total=Sum('amount'))['total'] or 0
    recent_fees = fees.select_related('student').order_by('-created_at')[:10]
    return render(request, 'accountant/dashboard.html', {
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_partial': total_partial,
        'total_records': fees.count(),
        'recent_fees': recent_fees,
    })


@login_required
def accountant_fees(request):
    if request.user.role != 'accountant':
        return redirect('core:dashboard')
    inst = request.user.institution
    fees = Fee.objects.filter(institution=inst).select_related('student').order_by('-created_at')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    if status:
        fees = fees.filter(status=status)
    if q:
        fees = fees.filter(Q(student__name__icontains=q))
    if request.method == 'POST' and request.POST.get('delete_id'):
        fid = request.POST.get('delete_id')
        try:
            f = Fee.objects.get(pk=fid, institution=inst)
            log_audit(request.user, 'delete_fee', f"Deleted fee record for {f.student.name}", 'fees')
            f.delete()
            messages.success(request, 'Fee record deleted.')
        except Fee.DoesNotExist:
            messages.error(request, 'Fee record not found.')
        return redirect('core:accountant_fees')
    return render(request, 'accountant/fees.html', {
        'fees': fees, 'status_filter': status, 'q': q,
    })


@login_required
def accountant_add_fee(request):
    if request.user.role != 'accountant':
        return redirect('core:dashboard')
    inst = request.user.institution
    students = Student.objects.filter(institution=inst).order_by('name')
    if request.method == 'POST':
        student_id = request.POST.get('student')
        amount = request.POST.get('amount', 0)
        due_date = request.POST.get('due_date', '')
        fee_type = request.POST.get('fee_type', 'Tuition')
        status = request.POST.get('status', 'Pending')
        description = request.POST.get('description', '').strip()
        errors = []
        if not student_id:
            errors.append('Please select a student.')
        if not amount or float(amount) <= 0:
            errors.append('Amount must be greater than 0.')
        if not due_date:
            errors.append('Due date is required.')
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accountant/add_fee.html', {'students': students})
        student = get_object_or_404(Student, pk=student_id, institution=inst)
        Fee.objects.create(
            institution=inst, student=student,
            amount=float(amount), due_date=due_date,
            fee_type=fee_type, status=status, description=description,
        )
        log_audit(request.user, 'add_fee', f"Added fee ₹{amount} for {student.name}", 'fees')
        messages.success(request, f'Fee record added for {student.name}.')
        return redirect('core:accountant_fees')
    return render(request, 'accountant/add_fee.html', {'students': students})


@login_required
def accountant_edit_fee(request, fee_id):
    if request.user.role != 'accountant':
        return redirect('core:dashboard')
    inst = request.user.institution
    fee = get_object_or_404(Fee, pk=fee_id, institution=inst)
    students = Student.objects.filter(institution=inst).order_by('name')
    if request.method == 'POST':
        fee.student_id = request.POST.get('student', fee.student_id)
        fee.amount = float(request.POST.get('amount', fee.amount))
        fee.due_date = request.POST.get('due_date', fee.due_date)
        fee.fee_type = request.POST.get('fee_type', fee.fee_type)
        fee.status = request.POST.get('status', fee.status)
        fee.description = request.POST.get('description', fee.description).strip()
        fee.save()
        log_audit(request.user, 'edit_fee', f"Updated fee for {fee.student.name}", 'fees')
        messages.success(request, 'Fee record updated.')
        return redirect('core:accountant_fees')
    return render(request, 'accountant/edit_fee.html', {'fee': fee, 'students': students})


@login_required
def accountant_collections(request):
    if request.user.role != 'accountant':
        return redirect('core:dashboard')
    inst = request.user.institution
    fees = Fee.objects.filter(institution=inst, status='Paid').select_related('student').order_by('-created_at')
    total = fees.aggregate(total=Sum('amount'))['total'] or 0
    by_type = fees.values('fee_type').annotate(total=Sum('amount'), count=Count('id'))
    return render(request, 'accountant/collections.html', {
        'fees': fees, 'total': total, 'by_type': by_type,
    })


# ─── EXAM VIEWS ────────────────────────────────────────────────

@login_required
def admin_exams(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    exams = Exam.objects.filter(institution=inst).select_related('course').order_by('-exam_date')
    q = request.GET.get('q', '').strip()
    if q:
        exams = exams.filter(Q(title__icontains=q) | Q(course__name__icontains=q) | Q(subject__icontains=q))
    if request.method == 'POST' and request.POST.get('delete_id'):
        eid = request.POST.get('delete_id')
        try:
            e = Exam.objects.get(pk=eid, institution=inst)
            log_audit(request.user, 'delete_exam', f"Deleted exam {e.title}", 'exams')
            e.delete()
            messages.success(request, 'Exam deleted.')
        except Exam.DoesNotExist:
            messages.error(request, 'Exam not found.')
        return redirect('core:admin_exams')
    return render(request, 'admin_panel/exams.html', {'exams': exams, 'q': q})


@login_required
def admin_add_exam(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    courses = Course.objects.filter(institution=inst).order_by('name')
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        course_id = request.POST.get('course', '')
        exam_type = request.POST.get('exam_type', 'Midterm')
        subject = request.POST.get('subject', '').strip()
        exam_date = request.POST.get('exam_date', '')
        total_marks = request.POST.get('total_marks', 100)
        passing_marks = request.POST.get('passing_marks', 40)
        errors = []
        if not title:
            errors.append('Title is required.')
        if not course_id:
            errors.append('Course is required.')
        if not exam_date:
            errors.append('Exam date is required.')
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'admin_panel/add_exam.html', {'courses': courses})
        course = get_object_or_404(Course, pk=course_id, institution=inst)
        Exam.objects.create(
            institution=inst, course=course, title=title,
            exam_type=exam_type, subject=subject, exam_date=exam_date,
            total_marks=int(total_marks), passing_marks=int(passing_marks),
        )
        log_audit(request.user, 'add_exam', f"Added exam {title}", 'exams')
        messages.success(request, f'Exam "{title}" created.')
        return redirect('core:admin_exams')
    return render(request, 'admin_panel/add_exam.html', {'courses': courses})


@login_required
def admin_exam_results(request, exam_id):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    exam = get_object_or_404(Exam, pk=exam_id, institution=inst)
    results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('student__name')
    students_in_course = StudentCourse.objects.filter(course=exam.course, institution=inst).select_related('student')
    existing_student_ids = results.values_list('student_id', flat=True)
    available_students = [sc.student for sc in students_in_course if sc.student_id not in existing_student_ids]
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'add':
            student_id = request.POST.get('student_id', '')
            marks = request.POST.get('marks', 0)
            remarks = request.POST.get('remarks', '').strip()
            if student_id:
                student = get_object_or_404(Student, pk=student_id, institution=inst)
                ExamResult.objects.update_or_create(
                    exam=exam, student=student,
                    defaults={'marks': float(marks), 'remarks': remarks, 'institution': inst},
                )
                log_audit(request.user, 'add_exam_result', f"Added result for {student.name} in {exam.title}", 'exam_results')
                messages.success(request, f'Result saved for {student.name}.')
        elif action == 'delete':
            rid = request.POST.get('result_id', '')
            try:
                r = ExamResult.objects.get(pk=rid, exam=exam, institution=inst)
                log_audit(request.user, 'delete_exam_result', f"Deleted result for {r.student.name}", 'exam_results')
                r.delete()
                messages.success(request, 'Result deleted.')
            except ExamResult.DoesNotExist:
                messages.error(request, 'Result not found.')
        return redirect('core:admin_exam_results', exam_id=exam.id)
    return render(request, 'admin_panel/exam_results.html', {
        'exam': exam, 'results': results, 'available_students': available_students,
    })


@login_required
def faculty_exams(request):
    if request.user.role != 'faculty':
        return redirect('core:dashboard')
    inst = request.user.institution
    try:
        faculty_obj = Faculty.objects.get(user=request.user, institution=inst)
    except Faculty.DoesNotExist:
        faculty_obj = None
    if faculty_obj:
        teaching_course_ids = faculty_obj.teachings.values_list('course_id', flat=True)
        exams = Exam.objects.filter(institution=inst, course_id__in=teaching_course_ids).select_related('course')
    else:
        exams = Exam.objects.none()
    return render(request, 'faculty/exams.html', {'exams': exams})


@login_required
def faculty_exam_results(request, exam_id):
    if request.user.role != 'faculty':
        return redirect('core:dashboard')
    inst = request.user.institution
    exam = get_object_or_404(Exam, pk=exam_id, institution=inst)
    results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('student__name')
    students_in_course = StudentCourse.objects.filter(course=exam.course, institution=inst).select_related('student')
    existing_student_ids = results.values_list('student_id', flat=True)
    available_students = [sc.student for sc in students_in_course if sc.student_id not in existing_student_ids]
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'add':
            student_id = request.POST.get('student_id', '')
            marks = request.POST.get('marks', 0)
            remarks = request.POST.get('remarks', '').strip()
            if student_id:
                student = get_object_or_404(Student, pk=student_id, institution=inst)
                ExamResult.objects.update_or_create(
                    exam=exam, student=student,
                    defaults={'marks': float(marks), 'remarks': remarks, 'institution': inst},
                )
                messages.success(request, f'Result saved for {student.name}.')
        elif action == 'delete':
            rid = request.POST.get('result_id', '')
            try:
                r = ExamResult.objects.get(pk=rid, exam=exam, institution=inst)
                r.delete()
                messages.success(request, 'Result deleted.')
            except ExamResult.DoesNotExist:
                messages.error(request, 'Result not found.')
        return redirect('core:faculty_exam_results', exam_id=exam.id)
    return render(request, 'faculty/exam_results.html', {
        'exam': exam, 'results': results, 'available_students': available_students,
    })


@login_required
def student_exams(request):
    if request.user.role != 'student':
        return redirect('core:dashboard')
    inst = request.user.institution
    try:
        student_obj = Student.objects.get(user=request.user, institution=inst)
    except Student.DoesNotExist:
        student_obj = None
    if not student_obj:
        return redirect('core:dashboard')
    my_courses = StudentCourse.objects.filter(student=student_obj, institution=inst).values_list('course_id', flat=True)
    exams = Exam.objects.filter(institution=inst, course_id__in=my_courses).select_related('course')
    my_results = ExamResult.objects.filter(student=student_obj, institution=inst).select_related('exam', 'exam__course')
    return render(request, 'student/exams.html', {
        'exams': exams, 'my_results': my_results, 'student_obj': student_obj,
    })


# ─── LIBRARY VIEWS ─────────────────────────────────────────────

@login_required
def admin_books(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    books = Book.objects.filter(institution=inst).order_by('title')
    q = request.GET.get('q', '').strip()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(category__icontains=q))
    if request.method == 'POST' and request.POST.get('delete_id'):
        bid = request.POST.get('delete_id')
        try:
            b = Book.objects.get(pk=bid, institution=inst)
            log_audit(request.user, 'delete_book', f"Deleted book {b.title}", 'books')
            b.delete()
            messages.success(request, 'Book deleted.')
        except Book.DoesNotExist:
            messages.error(request, 'Book not found.')
        return redirect('core:admin_books')
    return render(request, 'admin_panel/books.html', {'books': books, 'q': q})


@login_required
def admin_add_book(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        isbn = request.POST.get('isbn', '').strip()
        category = request.POST.get('category', '').strip()
        total_copies = request.POST.get('total_copies', 1)
        errors = []
        if not title:
            errors.append('Title is required.')
        if not author:
            errors.append('Author is required.')
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'admin_panel/add_book.html')
        Book.objects.create(
            institution=inst, title=title, author=author, isbn=isbn,
            category=category, total_copies=int(total_copies), available_copies=int(total_copies),
        )
        log_audit(request.user, 'add_book', f"Added book {title}", 'books')
        messages.success(request, f'Book "{title}" added.')
        return redirect('core:admin_books')
    return render(request, 'admin_panel/add_book.html')


@login_required
def admin_issue_book(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    books = Book.objects.filter(institution=inst, available_copies__gt=0).order_by('title')
    students = Student.objects.filter(institution=inst).order_by('name')
    if request.method == 'POST':
        book_id = request.POST.get('book', '')
        student_id = request.POST.get('student', '')
        due_date = request.POST.get('due_date', '')
        errors = []
        if not book_id:
            errors.append('Please select a book.')
        if not student_id:
            errors.append('Please select a student.')
        if not due_date:
            errors.append('Due date is required.')
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'admin_panel/issue_book.html', {'books': books, 'students': students})
        book = get_object_or_404(Book, pk=book_id, institution=inst)
        student = get_object_or_404(Student, pk=student_id, institution=inst)
        BookIssue.objects.create(
            institution=inst, book=book, student=student,
            issue_date=date.today(), due_date=due_date,
        )
        book.available_copies -= 1
        book.save()
        log_audit(request.user, 'issue_book', f"Issued {book.title} to {student.name}", 'book_issues')
        messages.success(request, f'Book issued to {student.name}.')
        return redirect('core:admin_book_issues')
    return render(request, 'admin_panel/issue_book.html', {'books': books, 'students': students})


@login_required
def admin_book_issues(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    issues = BookIssue.objects.filter(institution=inst).select_related('book', 'student').order_by('-issue_date')
    status = request.GET.get('status', '')
    if status:
        issues = issues.filter(status=status)
    if request.method == 'POST' and request.POST.get('return_id'):
        rid = request.POST.get('return_id')
        try:
            issue = BookIssue.objects.get(pk=rid, institution=inst, status='Issued')
            issue.status = 'Returned'
            issue.return_date = date.today()
            issue.save()
            issue.book.available_copies += 1
            issue.book.save()
            log_audit(request.user, 'return_book', f"Returned {issue.book.title} from {issue.student.name}", 'book_issues')
            messages.success(request, f'Book returned by {issue.student.name}.')
        except BookIssue.DoesNotExist:
            messages.error(request, 'Issue record not found.')
        return redirect('core:admin_book_issues')
    return render(request, 'admin_panel/book_issues.html', {'issues': issues, 'status_filter': status})


@login_required
def student_library(request):
    if request.user.role != 'student':
        return redirect('core:dashboard')
    inst = request.user.institution
    try:
        student_obj = Student.objects.get(user=request.user, institution=inst)
    except Student.DoesNotExist:
        student_obj = None
    if not student_obj:
        return redirect('core:dashboard')
    my_issues = BookIssue.objects.filter(student=student_obj, institution=inst).select_related('book').order_by('-issue_date')
    books = Book.objects.filter(institution=inst).order_by('title')
    return render(request, 'student/library.html', {
        'my_issues': my_issues, 'books': books,
    })


# ─── EVENT VIEWS ───────────────────────────────────────────────

@login_required
def admin_events(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    events = Event.objects.filter(institution=inst).order_by('-start_date')
    if request.method == 'POST' and request.POST.get('delete_id'):
        eid = request.POST.get('delete_id')
        try:
            ev = Event.objects.get(pk=eid, institution=inst)
            log_audit(request.user, 'delete_event', f"Deleted event {ev.title}", 'events')
            ev.delete()
            messages.success(request, 'Event deleted.')
        except Event.DoesNotExist:
            messages.error(request, 'Event not found.')
        return redirect('core:admin_events')
    return render(request, 'admin_panel/events.html', {'events': events})


@login_required
def admin_add_event(request):
    if request.user.role != 'admin':
        return redirect('core:dashboard')
    inst = request.user.institution
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        event_type = request.POST.get('event_type', 'Academic')
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')
        venue = request.POST.get('venue', '').strip()
        errors = []
        if not title:
            errors.append('Title is required.')
        if not start_date:
            errors.append('Start date is required.')
        if not end_date:
            errors.append('End date is required.')
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'admin_panel/add_event.html')
        Event.objects.create(
            institution=inst, title=title, description=description,
            event_type=event_type, start_date=start_date, end_date=end_date,
            venue=venue,
        )
        log_audit(request.user, 'add_event', f"Added event {title}", 'events')
        messages.success(request, f'Event "{title}" created.')
        return redirect('core:admin_events')
    return render(request, 'admin_panel/add_event.html')


@login_required
def faculty_events(request):
    if request.user.role != 'faculty':
        return redirect('core:dashboard')
    inst = request.user.institution
    events = Event.objects.filter(institution=inst).order_by('-start_date')
    return render(request, 'faculty/events.html', {'events': events})


@login_required
def student_events(request):
    if request.user.role != 'student':
        return redirect('core:dashboard')
    inst = request.user.institution
    events = Event.objects.filter(institution=inst).order_by('-start_date')
    return render(request, 'student/events.html', {'events': events})
