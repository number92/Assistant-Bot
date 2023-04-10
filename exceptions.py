class EmptyValueError(Exception):
    """Исключение для посого значения."""

    pass


class UnxpectedHTTPStatusError(ConnectionError):
    """Неожиданный статус код."""

    pass
