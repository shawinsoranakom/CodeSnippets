async def _auser_get_permissions(user, obj, from_name):
    permissions = set()
    name = "aget_%s_permissions" % from_name
    for backend in auth.get_backends():
        if hasattr(backend, name):
            permissions.update(await getattr(backend, name)(user, obj))
    return permissions