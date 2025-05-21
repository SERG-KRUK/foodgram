from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .constants import USERNAME_REGEX


def validate_year_not_future(value):
    """Ensure that the year is not in the future."""
    if value > datetime.now().year:
        raise ValidationError("Год создания не может быть больше текущего.")


def validate_username(value):
    """Validate the username."""
    if value.lower() == 'me':
        raise ValidationError('Имя пользователя "me" не разрешено.')
    RegexValidator(
        regex=USERNAME_REGEX,
        message='Недопустимые символы в имени пользователя.'
    )(value)


class UsernameValidationMixin:
    """Mixin for username validation."""

    def validate_username(self, username):
        """Validate the username."""
        validate_username(username)
        return username
