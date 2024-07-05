import os

from django.core.management.base import BaseCommand
from dotenv import find_dotenv, load_dotenv

from users.models import User

load_dotenv(find_dotenv())


class Command(BaseCommand):

    def handle(self, *args, **options):
        username = os.getenv('SUPERUSER_USERNAME')
        email = os.getenv('SUPERUSER_EMAIL')
        password = os.getenv('SUPERUSER_PASSWORD')

        if not User.objects.filter(username=username).exists():
            print('Создание супер-пользователя %s (%s)' % (username, email))
            User.objects.create_superuser(
                email=email, username=username, password=password
            )
        else:
            print('Супер-пользователь уже существует.')
