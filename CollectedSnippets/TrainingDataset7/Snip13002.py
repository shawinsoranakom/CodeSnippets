def __init__(self, redirect_to, preserve_request=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Location"] = iri_to_uri(redirect_to)
        redirect_to_str = str(redirect_to)
        if len(redirect_to_str) > MAX_URL_REDIRECT_LENGTH:
            raise DisallowedRedirect(
                f"Unsafe redirect exceeding {MAX_URL_REDIRECT_LENGTH} characters"
            )
        parsed = urlsplit(redirect_to_str)
        if preserve_request:
            self.status_code = self.status_code_preserve_request
        if parsed.scheme and parsed.scheme not in self.allowed_schemes:
            raise DisallowedRedirect(
                "Unsafe redirect to URL with protocol '%s'" % parsed.scheme
            )