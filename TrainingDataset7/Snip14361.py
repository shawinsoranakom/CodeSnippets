def django_file_prefixes():
    file = getattr(django, "__file__", None)
    if file is None:
        return ()
    return (os.path.dirname(file),)