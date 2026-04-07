def _mask_cipher_secret(secret):
    """
    Given a secret (assumed to be a string of CSRF_ALLOWED_CHARS), generate a
    token by adding a mask and applying it to the secret.
    """
    mask = _get_new_csrf_string()
    chars = CSRF_ALLOWED_CHARS
    pairs = zip((chars.index(x) for x in secret), (chars.index(x) for x in mask))
    cipher = "".join(chars[(x + y) % len(chars)] for x, y in pairs)
    return mask + cipher