from django.contrib.auth.management.commands.createsuperuser import (
    Command as BaseCommand)
from django.core.management import CommandError
from django.core.validators import validate_email


class Command(BaseCommand):
    help = 'Create a superuser with required first and last name'

    def handle(self, *args, **options):
        try:
            user_data = {}
            user_data['email'] = input("Email: ")
            validate_email(user_data['email'])
            
            user_data['username'] = input("Username: ")
            
            while True:
                user_data['first_name'] = input("First name: ")
                if user_data['first_name']:
                    break
                self.stderr.write("Error: First name cannot be blank")
            
            while True:
                user_data['last_name'] = input("Last name: ")
                if user_data['last_name']:
                    break
                self.stderr.write("Error: Last name cannot be blank")
            
            while True:
                password = input("Password: ")
                password2 = input("Password (again): ")
                if password == password2:
                    break
                self.stderr.write("Error: Passwords don't match")
            
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
