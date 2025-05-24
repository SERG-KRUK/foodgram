from django.core.management import BaseCommand
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Create a superuser with all required fields'

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write("Creating superuser...\n")
        
        # Email
        while True:
            email = input("Email: ")
            try:
                validate_email(email)
                if not User.objects.filter(email=email).exists():
                    break
                self.stderr.write(
                    "Error: Пользователь с таким email уже существует\n")
            except ValidationError:
                self.stderr.write(
                    "Error: Введите правильный адрес электронной почты\n")

        # Username
        while True:
            username = input("Username: ")
            if username and not User.objects.filter(username=username).exists():
                break
            self.stderr.write(
                "Error: Это поле не может быть пустым или имя занято\n")

        # First name
        while True:
            first_name = input("First name: ").strip()
            if first_name:
                break
            self.stderr.write("Error: Имя обязательно для заполнения\n")

        # Last name
        while True:
            last_name = input("Last name: ").strip()
            if last_name:
                break
            self.stderr.write("Error: Фамилия обязательна для заполнения\n")

        # Password
        while True:
            password = input("Password: ")
            password2 = input("Password (again): ")
            if password and password == password2:
                break
            self.stderr.write("Error: Пароли не совпадают или пустые\n")

        try:
            user = User.objects.create_superuser(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser {username} created successfully!")
            )
        except Exception as e:
            self.stderr.write(f"Error: {str(e)}\n")
