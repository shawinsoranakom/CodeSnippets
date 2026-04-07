def _security_middleware():
    return "django.middleware.security.SecurityMiddleware" in settings.MIDDLEWARE