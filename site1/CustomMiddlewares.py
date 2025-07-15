from django.utils.deprecation import MiddlewareMixin
from .logging_config import local_log_storage

class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        local_log_storage.user = getattr(request.user, 'username', 'Anonymous')
        local_log_storage.url = request.build_absolute_uri()
