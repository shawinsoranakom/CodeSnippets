def clear_caches():
    # Clear the warnings registry, so they can be displayed again
    for mod in sys.modules.values():
        if hasattr(mod, '__warningregistry__'):
            del mod.__warningregistry__

    # Flush standard output, so that buffered data is sent to the OS and
    # associated Python objects are reclaimed.
    for stream in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
        if stream is not None:
            stream.flush()

    try:
        re = sys.modules['re']
    except KeyError:
        pass
    else:
        re.purge()

    try:
        _strptime = sys.modules['_strptime']
    except KeyError:
        pass
    else:
        _strptime._regex_cache.clear()

    try:
        urllib_parse = sys.modules['urllib.parse']
    except KeyError:
        pass
    else:
        urllib_parse.clear_cache()

    try:
        urllib_request = sys.modules['urllib.request']
    except KeyError:
        pass
    else:
        urllib_request.urlcleanup()

    try:
        linecache = sys.modules['linecache']
    except KeyError:
        pass
    else:
        linecache.clearcache()

    try:
        mimetypes = sys.modules['mimetypes']
    except KeyError:
        pass
    else:
        mimetypes._default_mime_types()

    try:
        filecmp = sys.modules['filecmp']
    except KeyError:
        pass
    else:
        filecmp._cache.clear()

    try:
        struct = sys.modules['struct']
    except KeyError:
        pass
    else:
        struct._clearcache()

    try:
        doctest = sys.modules['doctest']
    except KeyError:
        pass
    else:
        doctest.master = None

    try:
        ctypes = sys.modules['ctypes']
    except KeyError:
        pass
    else:
        ctypes._reset_cache()

    try:
        typing = sys.modules['typing']
    except KeyError:
        pass
    else:
        for f in typing._cleanups:
            f()

        import inspect
        abs_classes = filter(inspect.isabstract, typing.__dict__.values())
        for abc in abs_classes:
            for obj in abc.__subclasses__() + [abc]:
                obj._abc_caches_clear()

    try:
        fractions = sys.modules['fractions']
    except KeyError:
        pass
    else:
        fractions._hash_algorithm.cache_clear()

    try:
        inspect = sys.modules['inspect']
    except KeyError:
        pass
    else:
        inspect._shadowed_dict_from_weakref_mro_tuple.cache_clear()
        inspect._filesbymodname.clear()
        inspect.modulesbyfile.clear()

    try:
        importlib_metadata = sys.modules['importlib.metadata']
    except KeyError:
        pass
    else:
        importlib_metadata.FastPath.__new__.cache_clear()

    try:
        encodings = sys.modules['encodings']
    except KeyError:
        pass
    else:
        encodings._cache.clear()

    try:
        codecs = sys.modules['codecs']
    except KeyError:
        pass
    else:
        # There's no direct API to clear the codecs search cache, but
        # `unregister` clears it implicitly.
        def noop_search_function(name):
            return None
        codecs.register(noop_search_function)
        codecs.unregister(noop_search_function)