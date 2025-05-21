"""
Константы для проекта.
"""


MAX_LENGTH_NAME = 256
MAX_LENGTH_SLUG = 50
MAX_LENGTH_USERNAME = 150
MAX_LENGTH_EMAIL = 254
MAX_LENGTH_CODE = 40

# Регулярные выражения
USERNAME_REGEX = r'^[\w.@+-]+\Z'
SLUG_REGEX = r'^[-a-zA-Z0-9_]+$'

# Валидация числовых значений
MIN_YEAR_VALUE = -3000  # Для поддержки древних произведений
MIN_SCORE_VALUE = 1
MAX_SCORE_VALUE = 10

# Длины строковых представлений
STR_SHORT_LENGTH = 20
STR_MEDIUM_LENGTH = 50

# Роли пользователей
USER = "user"
MODERATOR = "moderator"
ADMIN = "admin"

ROLE_CHOICES = (
    (USER, "Пользователь"),
    (MODERATOR, "Модератор"),
    (ADMIN, "Администратор"),
)
