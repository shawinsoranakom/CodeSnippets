def check_password(environ, username, password):
    """
    Authenticate against Django's auth database.

    mod_wsgi docs specify None, True, False as return value depending
    on whether the user exists and authenticates.

    Return None if the user does not exist, return False if the user exists but
    password is not correct, and return True otherwise.

    """
    # db connection state is managed similarly to the wsgi handler
    # as mod_wsgi may call these functions outside of a request/response cycle
    db.reset_queries()
    try:
        user = _get_user(username)
        if user:
            return user.check_password(password)
    finally:
        db.close_old_connections()