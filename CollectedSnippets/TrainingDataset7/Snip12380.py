def load_backend(backend_name):
    """
    Return a database backend's "base" module given a fully qualified database
    backend name, or raise an error if it doesn't exist.
    """
    # This backend was renamed in Django 1.9.
    if backend_name == "django.db.backends.postgresql_psycopg2":
        backend_name = "django.db.backends.postgresql"

    try:
        return import_module("%s.base" % backend_name)
    except ImportError as e_user:
        # The database backend wasn't found. Display a helpful error message
        # listing all built-in database backends.
        import django.db.backends

        builtin_backends = [
            name
            for _, name, ispkg in pkgutil.iter_modules(django.db.backends.__path__)
            if ispkg and name not in {"base", "dummy"}
        ]
        if backend_name not in ["django.db.backends.%s" % b for b in builtin_backends]:
            backend_reprs = map(repr, sorted(builtin_backends))
            raise ImproperlyConfigured(
                "%r isn't an available database backend or couldn't be "
                "imported. Check the above exception. To use one of the "
                "built-in backends, use 'django.db.backends.XXX', where XXX "
                "is one of:\n"
                "    %s" % (backend_name, ", ".join(backend_reprs))
            ) from e_user
        else:
            # If there's some other error, this must be an error in Django
            raise