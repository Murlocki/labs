import logging

from django.db import InterfaceError, OperationalError
from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class DatabaseUnavailableMiddleware:
    """Показывает страницу «Сервер базы данных недоступен» вместо ошибки 500 при потере связи с PostgreSQL."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (OperationalError, InterfaceError)):
            return None
        logger.error("Сервер базы данных недоступен: %s", exception)
        # шаблон рендерится без request: пользователь и сессия хранятся в недоступной БД
        return HttpResponse(render_to_string("analyses/db_unavailable.html"), status=503)
