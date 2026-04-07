def permission_required(perm, login_url=None, raise_exception=False):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """
    if isinstance(perm, str):
        perms = (perm,)
    else:
        perms = perm

    def decorator(view_func):
        if iscoroutinefunction(view_func):

            async def check_perms(user):
                # First check if the user has the permission (even anon users).
                if await user.ahas_perms(perms):
                    return True
                # In case the 403 handler should be called raise the exception.
                if raise_exception:
                    raise PermissionDenied
                # As the last resort, show the login form.
                return False

        else:

            def check_perms(user):
                # First check if the user has the permission (even anon users).
                if user.has_perms(perms):
                    return True
                # In case the 403 handler should be called raise the exception.
                if raise_exception:
                    raise PermissionDenied
                # As the last resort, show the login form.
                return False

        return user_passes_test(check_perms, login_url=login_url)(view_func)

    return decorator