from django.db import models
from django.utils import timezone


class Institution(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    inst_type = models.CharField(max_length=50, choices=[
        ('School', 'School'), ('College', 'College'), ('University', 'University'),
        ('Coaching', 'Coaching'), ('Other', 'Other'),
    ])
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'institutions'

    def __str__(self):
        return self.name


class Student(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='students')
    user = models.OneToOneField('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    name = models.CharField(max_length=200)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_details'
        ordering = ['name']

    def __str__(self):
        return self.name


class Faculty(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='faculty')
    user = models.OneToOneField('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='faculty_profile')
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    qualification = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'faculty_details'
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'courses'
        ordering = ['name']

    def __str__(self):
        return self.name


class Branch(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='branches')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'branches'
        ordering = ['name']

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Subject(models.Model):
    TYPE_CHOICES = [('Theory', 'Theory'), ('Lab', 'Lab'), ('Practical', 'Practical')]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='subjects')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='subjects')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    subject_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='Theory')
    year = models.CharField(max_length=50, blank=True)
    semester = models.CharField(max_length=50, blank=True)
    credits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['year', 'semester', 'name']

    def __str__(self):
        branch_part = f" ({self.branch.name})" if self.branch else ""
        year_part = f" Y{self.year} S{self.semester}" if self.year else ""
        return f"{self.name}{branch_part}{year_part}"


class FacultyTeaching(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='teachings')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='teachings')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    year = models.CharField(max_length=50)
    semester = models.CharField(max_length=50)
    designation = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'faculty_teaching'
        unique_together = ['faculty', 'course', 'subject', 'year', 'semester']

    def __str__(self):
        return f"{self.faculty.name} - {self.subject}"


class StudentCourse(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='student_courses')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'student_courses'
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.name} - {self.course.name}"


class Result(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D', 'D'), ('F', 'F'), (None, 'Not Graded'),
    ]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grade = models.CharField(max_length=5, choices=GRADE_CHOICES, null=True, blank=True)

    class Meta:
        db_table = 'results'
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.name} - {self.course.name}: {self.grade or 'N/A'}"


class Attendance(models.Model):
    STATUS_CHOICES = [('Present', 'Present'), ('Absent', 'Absent'), ('Late', 'Late')]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'attendance'
        unique_together = ['student', 'date']

    def __str__(self):
        return f"{self.student.name} - {self.date}: {self.status}"


class Fee(models.Model):
    STATUS_CHOICES = [('Paid', 'Paid'), ('Pending', 'Pending'), ('Partial', 'Partial')]
    TYPE_CHOICES = [
        ('Tuition', 'Tuition'), ('Exam', 'Exam'), ('Library', 'Library'),
        ('Hostel', 'Hostel'), ('Transport', 'Transport'), ('Other', 'Other'),
    ]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='fees')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    fee_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Tuition')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fees'
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.student.name} - ₹{self.amount} ({self.status})"


class Parent(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='parents')
    user = models.OneToOneField('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='parent_profile')
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=50, blank=True)
    child = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parents')

    class Meta:
        db_table = 'parents'

    def __str__(self):
        return f"{self.name} (Parent of {self.child.name})"


class AuditLog(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    username = models.CharField(max_length=150)
    role = models.CharField(max_length=20)
    details = models.TextField(blank=True)
    collection = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.action} by {self.username}"


class Exam(models.Model):
    TYPE_CHOICES = [
        ('Quiz', 'Quiz'), ('Assignment', 'Assignment'),
        ('Midterm', 'Midterm'), ('Final', 'Final'),
        ('Practical', 'Practical'), ('Other', 'Other'),
    ]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='exams')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Midterm')
    subject = models.CharField(max_length=200, blank=True)
    exam_date = models.DateField()
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exams'
        ordering = ['-exam_date']

    def __str__(self):
        return f"{self.title} ({self.course.name})"


class ExamResult(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='exam_results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    marks = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    remarks = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exam_results'
        unique_together = ['exam', 'student']

    def __str__(self):
        return f"{self.student.name} - {self.exam.title}: {self.marks}"

    @property
    def is_pass(self):
        return self.marks >= self.exam.passing_marks


class Book(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'books'
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author}"


class BookIssue(models.Model):
    STATUS_CHOICES = [('Issued', 'Issued'), ('Returned', 'Returned'), ('Overdue', 'Overdue')]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='book_issues')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_issues')
    issued_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_books')
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Issued')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'book_issues'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.student.name} - {self.book.title} ({self.status})"


class BookFine(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Paid', 'Paid')]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='book_fines')
    issue = models.ForeignKey(BookIssue, on_delete=models.CASCADE, related_name='fines')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_fines')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'book_fines'
        ordering = ['-created_at']

    def __str__(self):
        return f"Fine: {self.student.name} - ₹{self.amount} ({self.status})"


class Event(models.Model):
    TYPE_CHOICES = [
        ('Academic', 'Academic'), ('Cultural', 'Cultural'),
        ('Sports', 'Sports'), ('Workshop', 'Workshop'),
        ('Meeting', 'Meeting'), ('Other', 'Other'),
    ]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Academic')
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'events'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} ({self.start_date})"
