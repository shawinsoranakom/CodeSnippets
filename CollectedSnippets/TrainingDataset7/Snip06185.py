def _get_user(username):
    """
    Return the UserModel instance for `username`.

    If no matching user exists, or if the user is inactive, return None, in
    which case the default password hasher is run to mitigate timing attacks.
    """
    try:
        user = UserModel._default_manager.get_by_natural_key(username)
    except UserModel.DoesNotExist:
        user = None
    else:
        if not user.is_active:
            user = None

    if user is None:
        # Run the default password hasher once to reduce the timing difference
        # between existing/active and nonexistent/inactive users (#20760).
        UserModel().set_password("")

    return user