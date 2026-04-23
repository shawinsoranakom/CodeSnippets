def login_not_required(view_func):
    """
    Decorator for views that allows access to unauthenticated requests.
    """
    view_func.login_required = False
    return view_func