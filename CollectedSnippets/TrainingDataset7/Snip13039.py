def _does_token_match(request_csrf_token, csrf_secret):
    """
    Return whether the given CSRF token matches the given CSRF secret, after
    unmasking the token if necessary.

    This function assumes that the request_csrf_token argument has been
    validated to have the correct length (CSRF_SECRET_LENGTH or
    CSRF_TOKEN_LENGTH characters) and allowed characters, and that if it has
    length CSRF_TOKEN_LENGTH, it is a masked secret.
    """
    # Only unmask tokens that are exactly CSRF_TOKEN_LENGTH characters long.
    if len(request_csrf_token) == CSRF_TOKEN_LENGTH:
        request_csrf_token = _unmask_cipher_token(request_csrf_token)
    assert len(request_csrf_token) == CSRF_SECRET_LENGTH
    return constant_time_compare(request_csrf_token, csrf_secret)