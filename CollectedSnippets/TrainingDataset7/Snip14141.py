def is_django_module(module):
    """Return True if the given module is nested under Django."""
    return module.__name__.startswith("django.")