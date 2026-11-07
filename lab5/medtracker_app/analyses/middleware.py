import logging

from django.db import InterfaceError, OperationalError
from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class HttpAccessLogMiddleware:
    """Record request time, peer IP, method, path and response status."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.access_logger = logging.getLogger("http.access")

    def __call__(self, request):
        response = self.get_response(request)
        # Direct connection: do not trust a client-provided X-Forwarded-For.
        self.access_logger.info(
            "client_ip=%s method=%s path=%s status=%s",
            request.META.get("REMOTE_ADDR", "unknown"),
            request.method,
            request.path,
            response.status_code,
        )
        return response


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
