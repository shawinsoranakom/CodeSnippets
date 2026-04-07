def rotate_token(request):
    """
    Change the CSRF token in use for a request - should be done on login
    for security purposes.
    """
    _add_new_csrf_cookie(request)