def decorator(func):
        if permissions is not None:
            func.allowed_permissions = permissions
        if description is not None:
            func.short_description = description
        return func