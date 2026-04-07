def _xframe_middleware():
    return (
        "django.middleware.clickjacking.XFrameOptionsMiddleware" in settings.MIDDLEWARE
    )