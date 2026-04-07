def is_django_path(path):
    """Return True if the given file path is nested under Django."""
    return Path(django.__file__).parent in Path(path).parents