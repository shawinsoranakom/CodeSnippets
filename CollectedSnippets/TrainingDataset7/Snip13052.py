def _check_token(self, request):
        # Access csrf_secret via self._get_secret() as rotate_token() may have
        # been called by an authentication middleware during the
        # process_request() phase.
        try:
            csrf_secret = self._get_secret(request)
        except InvalidTokenFormat as exc:
            raise RejectRequest(f"CSRF cookie {exc.reason}.")

        if csrf_secret is None:
            # No CSRF cookie. For POST requests, we insist on a CSRF cookie,
            # and in this way we can avoid all CSRF attacks, including login
            # CSRF.
            raise RejectRequest(REASON_NO_CSRF_COOKIE)

        # Check non-cookie token for match.
        request_csrf_token = ""
        if request.method == "POST":
            try:
                request_csrf_token = request.POST.get("csrfmiddlewaretoken", "")
            except UnreadablePostError:
                # Handle a broken connection before we've completed reading the
                # POST data. process_view shouldn't raise any exceptions, so
                # we'll ignore and serve the user a 403 (assuming they're still
                # listening, which they probably aren't because of the error).
                pass

        if request_csrf_token == "":
            # Fall back to X-CSRFToken, to make things easier for AJAX, and
            # possible for PUT/DELETE.
            try:
                # This can have length CSRF_SECRET_LENGTH or CSRF_TOKEN_LENGTH,
                # depending on whether the client obtained the token from
                # the DOM or the cookie (and if the cookie, whether the cookie
                # was masked or unmasked).
                request_csrf_token = request.META[settings.CSRF_HEADER_NAME]
            except KeyError:
                raise RejectRequest(REASON_CSRF_TOKEN_MISSING)
            token_source = settings.CSRF_HEADER_NAME
        else:
            token_source = "POST"

        try:
            _check_token_format(request_csrf_token)
        except InvalidTokenFormat as exc:
            reason = self._bad_token_message(exc.reason, token_source)
            raise RejectRequest(reason)

        if not _does_token_match(request_csrf_token, csrf_secret):
            reason = self._bad_token_message("incorrect", token_source)
            raise RejectRequest(reason)