def __init__(self, get_response):
        if not apps.is_installed("django.contrib.sites"):
            raise ImproperlyConfigured(
                "You cannot use RedirectFallbackMiddleware when "
                "django.contrib.sites is not installed."
            )
        super().__init__(get_response)