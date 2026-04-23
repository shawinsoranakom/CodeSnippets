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