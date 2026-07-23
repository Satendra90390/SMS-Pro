from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('chairman', 'Chairman'),
        ('director', 'Director'),
        ('hod', 'Head of Department'),
        ('faculty', 'Faculty'),
        ('student', 'Student'),
        ('librarian', 'Librarian'),
        ('accountant', 'Accountant'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    institution = models.ForeignKey('core.Institution', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
