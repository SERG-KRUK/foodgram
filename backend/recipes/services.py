"""Генератор случайной строки для коротких ссылок."""

import string
from random import choice, randint


def generate_hash() -> str:
    """Генерирует случайную строку для коротких ссылок."""
    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(15, 32)))
