def get_cookie_signer(salt="django.core.signing.get_cookie_signer"):
    Signer = import_string(settings.SIGNING_BACKEND)
    return Signer(
        key=_cookie_signer_key(settings.SECRET_KEY),
        fallback_keys=map(_cookie_signer_key, settings.SECRET_KEY_FALLBACKS),
        salt=salt,
    )