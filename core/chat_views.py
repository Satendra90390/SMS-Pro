import json
import os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from .models import (
    Student, Faculty, Course, Attendance, Result, Fee,
    StudentCourse, FacultyTeaching,
)


def build_context(user):
    inst = user.institution
    ctx_parts = []

    if user.role == 'admin':
        student_count = Student.objects.filter(institution=inst).count()
        faculty_count = Faculty.objects.filter(institution=inst).count()
        course_count = Course.objects.filter(institution=inst).count()
        present = Attendance.objects.filter(institution=inst, status='Present').count()
        total_att = Attendance.objects.filter(institution=inst).count()
        rate = round(present / total_att * 100, 1) if total_att else 0
        fees = Fee.objects.filter(institution=inst)
        collected = fees.filter(status='Paid').aggregate(t=Sum('amount'))['t'] or 0
        total = fees.aggregate(t=Sum('amount'))['t'] or 0
        failed = Result.objects.filter(institution=inst, grade__in=['F', 'E', 'D']).count()
        ctx_parts.append(
            f"You are an AI assistant for '{inst.name}' (SMS Pro). "
            f"Current stats: {student_count} students, {faculty_count} faculty, "
            f"{course_count} courses, {rate}% attendance rate, "
            f"₹{collected:,} collected of ₹{total:,} total fees, "
            f"{failed} students with failing grades."
        )

    elif user.role == 'student':
        try:
            s = Student.objects.get(user=user, institution=inst)
        except Student.DoesNotExist:
            s = None
        if s:
            results = Result.objects.filter(student=s, institution=inst).select_related('course')
            fees = Fee.objects.filter(student=s, institution=inst)
            att = Attendance.objects.filter(student=s, institution=inst)
            att_total = att.count()
            att_present = att.filter(status='Present').count()
            res_lines = [f"  - {r.course.name}: {r.grade} ({r.marks}/{r.total_marks})" for r in results]
            fee_lines = [f"  - {f.course.name}: Rs {f.amount} ({f.status})" for f in fees]
            ctx_parts.append(
                f"You are an AI assistant for student '{s.name}' at '{inst.name}'. "
                f"Age: {s.age}, Phone: {s.phone}. "
                f"Attendance: {att_present}/{att_total} ({round(att_present/att_total*100,1) if att_total else 0}%). "
                f"Results:\n" + "\n".join(res_lines or ["  No results yet"]) +
                f"\nFees:\n" + "\n".join(fee_lines or ["  No fee records"])
            )

    elif user.role == 'faculty':
        try:
            f = Faculty.objects.get(user=user, institution=inst)
        except Faculty.DoesNotExist:
            f = None
        if f:
            teachings = FacultyTeaching.objects.filter(faculty=f, institution=inst).select_related('course')
            course_names = [t.course.name for t in teachings]
            student_count = Student.objects.filter(institution=inst).count()
            ctx_parts.append(
                f"You are an AI assistant for faculty member '{f.name}' (Dept: {f.department}) at '{inst.name}'. "
                f"Teaching: {', '.join(course_names or ['None'])}. "
                f"Total students in institution: {student_count}."
            )

    elif user.role == 'parent':
        ctx_parts.append(
            f"You are an AI assistant for a parent at '{inst.name}'. "
            f"You can help with general information about the institution."
        )

    return " ".join(ctx_parts) if ctx_parts else "You are an AI assistant for SMS Pro student management system."


@login_required
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)

    api_key = os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'AI is not configured. Ask admin to set GEMINI_API_KEY.'}, status=500)

    system_prompt = build_context(request.user)
    history = data.get('history', [])

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt + "\nKeep responses concise and helpful. Use bullet points when listing data. You are part of SMS Pro — a student management system. Only answer questions related to the institution, students, academics, or SMS Pro features. Politely redirect unrelated questions."
        )
        chat = model.start_chat(history=history)
        response = chat.send_message(user_message)
        return JsonResponse({'reply': response.text})
    except Exception as e:
        return JsonResponse({'error': f'AI error: {str(e)}'}, status=500)
