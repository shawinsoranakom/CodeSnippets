def get_finder(import_path):
    """
    Import the staticfiles finder class described by import_path, where
    import_path is the full Python path to the class.
    """
    Finder = import_string(import_path)
    if not issubclass(Finder, BaseFinder):
        raise ImproperlyConfigured(
            'Finder "%s" is not a subclass of "%s"' % (Finder, BaseFinder)
        )
    return Finder()