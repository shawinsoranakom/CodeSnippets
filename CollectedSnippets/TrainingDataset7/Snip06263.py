def get_login_url(self, view_func):
        login_url = getattr(view_func, "login_url", None) or settings.LOGIN_URL
        if not login_url:
            raise ImproperlyConfigured(
                "No login URL to redirect to. Define settings.LOGIN_URL or "
                "provide a login_url via the 'django.contrib.auth.decorators."
                "login_required' decorator."
            )
        return str(login_url)