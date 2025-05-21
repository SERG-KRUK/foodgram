from django.core.mail import send_mail
from django.conf import settings


def send_confirmation_email(email, confirmation_code):
    """send code conf"""
    send_mail(
        'Confirmation code',
        f'Your code: {confirmation_code}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
