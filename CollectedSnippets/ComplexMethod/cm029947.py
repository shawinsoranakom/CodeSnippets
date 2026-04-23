def safeimport(path, forceload=0, cache={}):
    """Import a module; handle errors; return None if the module isn't found.

    If the module *is* found but an exception occurs, it's wrapped in an
    ErrorDuringImport exception and reraised.  Unlike __import__, if a
    package path is specified, the module at the end of the path is returned,
    not the package at the beginning.  If the optional 'forceload' argument
    is 1, we reload the module from disk (unless it's a dynamic extension)."""
    try:
        # If forceload is 1 and the module has been previously loaded from
        # disk, we always have to reload the module.  Checking the file's
        # mtime isn't good enough (e.g. the module could contain a class
        # that inherits from another module that has changed).
        if forceload and path in sys.modules:
            if path not in sys.builtin_module_names:
                # Remove the module from sys.modules and re-import to try
                # and avoid problems with partially loaded modules.
                # Also remove any submodules because they won't appear
                # in the newly loaded module's namespace if they're already
                # in sys.modules.
                subs = [m for m in sys.modules if m.startswith(path + '.')]
                for key in [path] + subs:
                    # Prevent garbage collection.
                    cache[key] = sys.modules[key]
                    del sys.modules[key]
        module = importlib.import_module(path)
    except BaseException as err:
        # Did the error occur before or after the module was found?
        if path in sys.modules:
            # An error occurred while executing the imported module.
            raise ErrorDuringImport(sys.modules[path].__file__, err)
        elif type(err) is SyntaxError:
            # A SyntaxError occurred before we could execute the module.
            raise ErrorDuringImport(err.filename, err)
        elif isinstance(err, ImportError) and err.name == path:
            # No such module in the path.
            return None
        else:
            # Some other error occurred during the importing process.
            raise ErrorDuringImport(path, err)
    return module