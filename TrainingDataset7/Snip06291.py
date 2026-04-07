async def _auser_has_perm(user, perm, obj):
    """See _user_has_perm()"""
    for backend in auth.get_backends():
        if not hasattr(backend, "ahas_perm"):
            continue
        try:
            if await backend.ahas_perm(user, perm, obj):
                return True
        except PermissionDenied:
            return False
    return False