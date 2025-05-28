"""Константы для проекта."""

# Регулярные выражения
USERNAME_REGEX = r'^[\w.@+-]+\Z'
SLUG_REGEX = r'^[-a-zA-Z0-9_]+$'

# Валидация числовых значений
MIN_YEAR_VALUE = -3000  # Для поддержки древних произведений
MIN_SCORE_VALUE = 1
MAX_SCORE_VALUE = 10

# Длины строковых представлений
TAG = 32
INGREDIENT = 128
MEASUREMENT_UNIT = 64
RECIPE_NAME = 256
EMAIL = 254
USERNAME = 150
FIRST_NAME = 150
LAST_NAME = 150
SHORT_URL_CODE = 6
