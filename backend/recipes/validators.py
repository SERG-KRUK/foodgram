from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .constants import USERNAME_REGEX


def validate_year_not_future(value):
    """Проверяет, что год не в будущем"""
    if value > datetime.now().year:
        raise ValidationError("Год создания не может быть больше текущего.")


def validate_username(value):
    """Валидация имени пользователя."""
    if value.lower() == 'me':
        raise ValidationError('Имя пользователя "me" не разрешено.')
    RegexValidator(
        regex=USERNAME_REGEX,
        message='Недопустимые символы в имени пользователя.'
    )(value)


class UsernameValidationMixin:
    """Миксин для валидации имени пользователя."""

    def validate_username(self, username):
        validate_username(username)
        return username