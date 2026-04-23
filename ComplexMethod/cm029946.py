def synopsis(filename, cache={}):
    """Get the one-line summary out of a module file."""
    mtime = os.stat(filename).st_mtime
    lastupdate, result = cache.get(filename, (None, None))
    if lastupdate is None or lastupdate < mtime:
        # Look for binary suffixes first, falling back to source.
        if filename.endswith(tuple(importlib.machinery.BYTECODE_SUFFIXES)):
            loader_cls = importlib.machinery.SourcelessFileLoader
        elif filename.endswith(tuple(importlib.machinery.EXTENSION_SUFFIXES)):
            loader_cls = importlib.machinery.ExtensionFileLoader
        else:
            loader_cls = None
        # Now handle the choice.
        if loader_cls is None:
            # Must be a source file.
            try:
                file = tokenize.open(filename)
            except OSError:
                # module can't be opened, so skip it
                return None
            # text modules can be directly examined
            with file:
                result = source_synopsis(file)
        else:
            # Must be a binary module, which has to be imported.
            loader = loader_cls('__temp__', filename)
            # XXX We probably don't need to pass in the loader here.
            spec = importlib.util.spec_from_file_location('__temp__', filename,
                                                          loader=loader)
            try:
                module = importlib._bootstrap._load(spec)
            except:
                return None
            del sys.modules['__temp__']
            result = module.__doc__.splitlines()[0] if module.__doc__ else None
        # Cache the result.
        cache[filename] = (mtime, result)
    return result