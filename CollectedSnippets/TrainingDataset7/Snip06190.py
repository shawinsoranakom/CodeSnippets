def check_password(password, encoded, setter=None, preferred="default"):
    """
    Return a boolean of whether the raw password matches the three part encoded
    digest.

    If setter is specified, it'll be called when you need to regenerate the
    password.
    """
    is_correct, must_update = verify_password(password, encoded, preferred=preferred)
    if setter and is_correct and must_update:
        setter(password)
    return is_correct