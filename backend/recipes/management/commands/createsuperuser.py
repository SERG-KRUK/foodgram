from django.core.management import BaseCommand
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Create a superuser with all required fields'

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write("Creating superuser...\n")
        
        # Email validation with retry
        email = self._get_valid_email(User)
        
        # Username validation with retry
        username = self._get_valid_username(User)
        
        # Required fields validation
        first_name = self._get_valid_input(
            "First name: ", "Имя обязательно для заполнения")
        last_name = self._get_valid_input(
            "Last name: ", "Фамилия обязательна для заполнения")
        
        # Password validation
        password = self._get_valid_password()
        
        # Create superuser
        self._create_superuser(
            User,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

    def _get_valid_email(self, User):
        """Validate and return email."""
        while True:
            email = input("Email: ").strip()
            try:
                validate_email(email)
                if not User.objects.filter(email=email).exists():
                    return email
                self.stderr.write(
                    "Error: Пользователь с таким email уже существует\n")
            except ValidationError:
                self.stderr.write(
                    "Error: Введите правильный адрес электронной почты\n")

    def _get_valid_username(self, User):
        """Validate and return username."""
        while True:
            username = input("Username: ").strip()
            if username:
                if not User.objects.filter(username=username).exists():
                    return username
                self.stderr.write("Error: Имя пользователя уже занято\n")
            else:
                self.stderr.write("Error: Это поле не может быть пустым\n")

    def _get_valid_input(self, prompt, error_message):
        """Get non-empty input."""
        while True:
            value = input(prompt).strip()
            if value:
                return value
            self.stderr.write(f"Error: {error_message}\n")

    def _get_valid_password(self):
        """Validate and return password."""
        while True:
            password = input("Password: ").strip()
            password2 = input("Password (again): ").strip()
            if password and password == password2:
                return password
            self.stderr.write("Error: Пароли не совпадают или пустые\n")

    def _create_superuser(self, User, **kwargs):
        """Create superuser with given parameters."""
        try:
            user = User.objects.create_superuser(**kwargs)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser {kwargs['username']} created successfully!"
                )
            )
            return user  # Теперь переменная используется
        except Exception as e:
            self.stderr.write(f"Error: {str(e)}\n")
            raise
