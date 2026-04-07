def process_response(self, request, response):
        if request.META.get("CSRF_COOKIE_NEEDS_UPDATE"):
            self._set_csrf_cookie(request, response)
            # Unset the flag to prevent _set_csrf_cookie() from being
            # unnecessarily called again in process_response() by other
            # instances of CsrfViewMiddleware. This can happen e.g. when both a
            # decorator and middleware are used. However,
            # CSRF_COOKIE_NEEDS_UPDATE is still respected in subsequent calls
            # e.g. in case rotate_token() is called in process_response() later
            # by custom middleware but before those subsequent calls.
            request.META["CSRF_COOKIE_NEEDS_UPDATE"] = False

        return response