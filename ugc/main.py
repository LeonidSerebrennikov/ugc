import os
import sys
import time
import django
from django.core.management import execute_from_command_line
from django.db import connections
from django.db.utils import OperationalError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ugc.settings')

def wait_for_db():
    for _ in range(60):
        try:
            connections['default'].cursor()
            return
        except OperationalError:
            time.sleep(1)
    sys.exit(1)

def run_migrations():
    execute_from_command_line(['manage.py', 'migrate'])

def create_superuser():
    django.setup()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)

def main():
    wait_for_db()
    run_migrations()
    create_superuser()
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

if __name__ == '__main__':
    main()