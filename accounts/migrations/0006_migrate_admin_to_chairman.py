from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='admin').update(role='chairman')


def backwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='chairman').update(role='admin')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_user_role'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
