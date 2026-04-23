def module_dir(module):
    """
    Find the name of the directory that contains a module, if possible.

    Raise ValueError otherwise, e.g. for namespace packages that are split
    over several directories.
    """
    # Convert to list because __path__ may not support indexing.
    paths = list(getattr(module, "__path__", []))
    if len(paths) == 1:
        return paths[0]
    else:
        filename = getattr(module, "__file__", None)
        if filename is not None:
            return os.path.dirname(filename)
    raise ValueError("Cannot determine directory containing %s" % module)