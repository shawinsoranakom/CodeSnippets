def auth_password_validators_changed(*, setting, **kwargs):
    if setting == "AUTH_PASSWORD_VALIDATORS":
        from django.contrib.auth.password_validation import (
            get_default_password_validators,
        )

        get_default_password_validators.cache_clear()