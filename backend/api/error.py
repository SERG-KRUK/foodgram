"""Конфигурация приложения api."""

class MinValue:
    COOKING_TIME = 1
    AMOUNT = 1


class Error:
    COOKING_TIME = f'Не менее {MinValue.COOKING_TIME} мин. приготовления'
    AMOUNT = f'Не менее {MinValue.AMOUNT} ед. ингредиента'
    ALREADY_IN_SHOPPING_CART = 'Рецепт уже есть в списке покупок'
    ALREADY_FAVORITED = 'Рецепт уже есть в избранном'
    NOT_IN_SHOPPING_CART = 'Рецепта нет в списке покупок'
    NOT_FAVORITED = 'Рецепта нет в избранном'
    ALREADY_SUBSCRIBED = 'Вы уже подписаны на этого автора'
    CANNOT_SUBSCRIBE_TO_YOURSELF = 'Нельзя подписаться на самого себя'
    DUPLICATES = 'Дубликаты: {}'
    NO_IMAGE = 'Поле "image" не может быть пустым'
    NOT_SUBSCRIBED = 'Вы не подписаны на этого автора'
    NO_TAGS = 'Нужен хотя бы один тег'
    NO_INGREDIENTS = 'Рецепт не может обойтись без продуктов'
    NOT_EXIST = 'Рецепт не существует'
    SHORT_URL_CODE = 'Не удалось сгенерировать уникальный код'
    SHORT_URL_CODE_GEN = (
        'Превышено количество попыток генерации short_url_code.'
    )
