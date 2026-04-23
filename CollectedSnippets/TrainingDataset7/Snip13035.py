def _add_new_csrf_cookie(request):
    """Generate a new random CSRF_COOKIE value, and add it to request.META."""
    csrf_secret = _get_new_csrf_string()
    request.META.update(
        {
            "CSRF_COOKIE": csrf_secret,
            "CSRF_COOKIE_NEEDS_UPDATE": True,
        }
    )
    return csrf_secret