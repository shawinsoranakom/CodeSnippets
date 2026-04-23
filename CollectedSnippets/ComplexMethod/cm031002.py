def dash_R_cleanup(fs, ps, pic, zdc, abcs, linecache_data):
    import copyreg
    import collections.abc

    # Restore some original values.
    warnings.filters[:] = fs
    copyreg.dispatch_table.clear()
    copyreg.dispatch_table.update(ps)
    sys.path_importer_cache.clear()
    sys.path_importer_cache.update(pic)
    lcache, linteractive = linecache_data
    linecache._interactive_cache.clear()
    linecache._interactive_cache.update(linteractive)
    linecache.cache.clear()
    linecache.cache.update(lcache)
    try:
        import zipimport
    except ImportError:
        pass # Run unmodified on platforms without zipimport support
    else:
        zipimport._zip_directory_cache.clear()
        zipimport._zip_directory_cache.update(zdc)

    # Clear ABC registries, restoring previously saved ABC registries.
    abs_classes = [getattr(collections.abc, a) for a in collections.abc.__all__]
    with warnings.catch_warnings(action='ignore', category=DeprecationWarning):
        abs_classes.append(collections.abc.ByteString)
    abs_classes = filter(isabstract, abs_classes)
    for abc in abs_classes:
        for obj in abc.__subclasses__() + [abc]:
            refs = abcs.get(obj, None)
            if refs is not None:
                obj._abc_registry_clear()
                for ref in refs:
                    subclass = ref()
                    if subclass is not None:
                        obj.register(subclass)
            obj._abc_caches_clear()

    # Clear caches
    clear_caches()

    # Clear other caches last (previous function calls can re-populate them):
    sys._clear_internal_caches()