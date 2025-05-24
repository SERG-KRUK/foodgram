"""Api утилита для ошибки ингридиентов кол-ва."""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Api custom handler."""
    response = exception_handler(exc, context)

    if response is not None:
        if 'ingredients' in response.data:
            # Если ошибка в ингредиентах, берём первую и возвращаем как "error"
            error_message = response.data['ingredients'][0]
            response.data = {'error': error_message}
        elif 'non_field_errors' in response.data:
            # Обработка других non-field ошибок
            response.data = {'error': response.data['non_field_errors'][0]}

    return response
