def process_request(self, request):
        try:
            csrf_secret = self._get_secret(request)
        except InvalidTokenFormat:
            _add_new_csrf_cookie(request)
        else:
            if csrf_secret is not None:
                # Use the same secret next time. If the secret was originally
                # masked, this also causes it to be replaced with the unmasked
                # form, but only in cases where the secret is already getting
                # saved anyways.
                request.META["CSRF_COOKIE"] = csrf_secret