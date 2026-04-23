def _session_middleware():
    return "django.contrib.sessions.middleware.SessionMiddleware" in settings.MIDDLEWARE