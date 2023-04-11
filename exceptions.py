class EmptyValueError(Exception):
    """Исключение для пустого значения."""

    pass


class UnxpectedHTTPStatusError(ConnectionError):
    """Неожиданный статус код."""

    pass
