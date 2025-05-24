from django.contrib.auth.management.commands.createsuperuser import (
    Command as BaseCommand)
from django.core.management import CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Create a superuser with required fields'

    def handle(self, *args, **options):
        user_data = {}
        
        try:
            # Email validation
            while True:
                user_data['email'] = input("Email: ")
                try:
                    validate_email(user_data['email'])
                    break
                except ValidationError:
                    self.stderr.write(
                        "Error: Введите правильный адрес электронной почты.")

            # Username
            user_data['username'] = input("Username: ")
            
            # First name (required)
            while True:
                user_data['first_name'] = input("First name: ").strip()
                if user_data['first_name']:
                    break
                self.stderr.write("Error: Имя обязательно для заполнения")

            # Last name (required)
            while True:
                user_data['last_name'] = input("Last name: ").strip()
                if user_data['last_name']:
                    break
                self.stderr.write("Error: Фамилия обязательна для заполнения")

            # Password
            while True:
                password = input("Password: ")
                password2 = input("Password (again): ")
                if password and password == password2:
                    break
                self.stderr.write("Error: Пароли не совпадают или пустые")

            from django.contrib.auth import get_user_model
            User = get_user_model()

            user = User.objects.create_superuser(
                email=user_data['email'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password=password
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser {user.username} created successfully")
            )

        except KeyboardInterrupt:
            self.stderr.write("\nOperation cancelled")
        except Exception as e:
            raise CommandError(f"Error: {str(e)}")
