import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Run migrations, create site, and create default admin user'

    def handle(self, *args, **options):
        self.stdout.write('Running migrations...')
        call_command('migrate', '--noinput')

        self.stdout.write('Ensuring site exists...')
        site, _ = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost'),
                'name': 'Edosaic',
            }
        )
        site.domain = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')
        site.name = 'Edosaic'
        site.save()

        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('Creating admin user...')
            User.objects.create_superuser(
                username='admin',
                email='admin@smspro.com',
                password='admin123',
            )
            self.stdout.write(self.style.SUCCESS('Admin user created: admin / admin123'))
        else:
            self.stdout.write('Admin user already exists.')
