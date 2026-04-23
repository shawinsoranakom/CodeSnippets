def check_middleware(app_configs, **kwargs):
    errors = []

    login_required_index = _subclass_index(
        "django.contrib.auth.middleware.LoginRequiredMiddleware",
        settings.MIDDLEWARE,
    )

    if login_required_index != -1:
        auth_index = _subclass_index(
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            settings.MIDDLEWARE,
        )
        if auth_index == -1 or auth_index > login_required_index:
            errors.append(
                checks.Error(
                    "In order to use django.contrib.auth.middleware."
                    "LoginRequiredMiddleware, django.contrib.auth.middleware."
                    "AuthenticationMiddleware must be defined before it in MIDDLEWARE.",
                    id="auth.E013",
                )
            )
    return errors