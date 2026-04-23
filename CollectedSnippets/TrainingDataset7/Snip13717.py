def _class_shuffle_key(cls):
    return f"{cls.__module__}.{cls.__qualname__}"