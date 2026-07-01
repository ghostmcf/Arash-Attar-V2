import logging
import threading

local_log_storage = threading.local()

class RequestLogFilter(logging.Filter):
    def filter(self, record):
        record.username = getattr(local_log_storage, 'user', 'Unknown')
        record.url = getattr(local_log_storage, 'url', 'No URL')
        return True