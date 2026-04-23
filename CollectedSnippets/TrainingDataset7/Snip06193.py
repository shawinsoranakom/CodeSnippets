def get_hashers():
    hashers = []
    for hasher_path in settings.PASSWORD_HASHERS:
        hasher_cls = import_string(hasher_path)
        hasher = hasher_cls()
        if not getattr(hasher, "algorithm"):
            raise ImproperlyConfigured(
                "hasher doesn't specify an algorithm name: %s" % hasher_path
            )
        hashers.append(hasher)
    return hashers