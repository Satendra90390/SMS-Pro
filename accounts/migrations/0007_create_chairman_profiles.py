from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Chairman = apps.get_model('core', 'Chairman')
    for user in User.objects.filter(role='chairman'):
        if not Chairman.objects.filter(user=user).exists() and user.institution:
            Chairman.objects.get_or_create(
                institution=user.institution,
                defaults={
                    'user': user,
                    'name': user.get_full_name() or user.username,
                    'phone': getattr(user, 'phone', ''),
                    'email': user.email or '',
                },
            )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_migrate_admin_to_chairman'),
        ('core', '0006_faculty_courses_faculty_mentors_faculty_semester_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
