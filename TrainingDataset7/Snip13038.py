def _check_token_format(token):
    """
    Raise an InvalidTokenFormat error if the token has an invalid length or
    characters that aren't allowed. The token argument can be a CSRF cookie
    secret or non-cookie CSRF token, and either masked or unmasked.
    """
    if len(token) not in (CSRF_TOKEN_LENGTH, CSRF_SECRET_LENGTH):
        raise InvalidTokenFormat(REASON_INCORRECT_LENGTH)
    # Make sure all characters are in CSRF_ALLOWED_CHARS.
    if invalid_token_chars_re.search(token):
        raise InvalidTokenFormat(REASON_INVALID_CHARACTERS)