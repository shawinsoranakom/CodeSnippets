def _bad_token_message(self, reason, token_source):
        if token_source != "POST":
            # Assume it is a settings.CSRF_HEADER_NAME value.
            header_name = HttpHeaders.parse_header_name(token_source)
            token_source = f"the {header_name!r} HTTP header"
        return f"CSRF token from {token_source} {reason}."