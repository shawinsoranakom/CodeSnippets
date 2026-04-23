def _csrf_middleware():
    return "django.middleware.csrf.CsrfViewMiddleware" in settings.MIDDLEWARE