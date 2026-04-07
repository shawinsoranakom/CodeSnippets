def _set_csrf_cookie(self, request, response):
        if settings.CSRF_USE_SESSIONS:
            if request.session.get(CSRF_SESSION_KEY) != request.META["CSRF_COOKIE"]:
                request.session[CSRF_SESSION_KEY] = request.META["CSRF_COOKIE"]
        else:
            response.set_cookie(
                settings.CSRF_COOKIE_NAME,
                request.META["CSRF_COOKIE"],
                max_age=settings.CSRF_COOKIE_AGE,
                domain=settings.CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=settings.CSRF_COOKIE_SECURE,
                httponly=settings.CSRF_COOKIE_HTTPONLY,
                samesite=settings.CSRF_COOKIE_SAMESITE,
            )
            # Set the Vary header since content varies with the CSRF cookie.
            patch_vary_headers(response, ("Cookie",))