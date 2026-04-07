async def _auser_has_module_perms(user, app_label):
    """See _user_has_module_perms()"""
    for backend in auth.get_backends():
        if not hasattr(backend, "ahas_module_perms"):
            continue
        try:
            if await backend.ahas_module_perms(user, app_label):
                return True
        except PermissionDenied:
            return False
    return False