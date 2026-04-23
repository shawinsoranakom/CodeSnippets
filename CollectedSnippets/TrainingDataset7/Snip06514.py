def _trailing_slash_required(self):
        return (
            settings.APPEND_SLASH
            and "django.middleware.common.CommonMiddleware" in settings.MIDDLEWARE
        )