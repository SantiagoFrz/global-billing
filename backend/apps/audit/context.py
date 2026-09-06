from contextvars import ContextVar

request_user = ContextVar("request_user", default=None)
request_ip = ContextVar("request_ip", default=None)
