def extend_path(path, name):
    """Extend a package's path.

    Intended use is to place the following code in a package's __init__.py:

        from pkgutil import extend_path
        __path__ = extend_path(__path__, __name__)

    For each directory on sys.path that has a subdirectory that
    matches the package name, add the subdirectory to the package's
    __path__.  This is useful if one wants to distribute different
    parts of a single logical package as multiple directories.

    It also looks for *.pkg files beginning where * matches the name
    argument.  This feature is similar to *.pth files (see site.py),
    except that it doesn't special-case lines starting with 'import'.
    A *.pkg file is trusted at face value: apart from checking for
    duplicates, all entries found in a *.pkg file are added to the
    path, regardless of whether they are exist the filesystem.  (This
    is a feature.)

    If the input path is not a list (as is the case for frozen
    packages) it is returned unchanged.  The input path is not
    modified; an extended copy is returned.  Items are only appended
    to the copy at the end.

    It is assumed that sys.path is a sequence.  Items of sys.path that
    are not (unicode or 8-bit) strings referring to existing
    directories are ignored.  Unicode items of sys.path that cause
    errors when used as filenames may cause this function to raise an
    exception (in line with os.path.isdir() behavior).
    """

    if not isinstance(path, list):
        # This could happen e.g. when this is called from inside a
        # frozen package.  Return the path unchanged in that case.
        return path

    sname_pkg = name + ".pkg"

    path = path[:] # Start with a copy of the existing path

    parent_package, _, final_name = name.rpartition('.')
    if parent_package:
        try:
            search_path = sys.modules[parent_package].__path__
        except (KeyError, AttributeError):
            # We can't do anything: find_loader() returns None when
            # passed a dotted name.
            return path
    else:
        search_path = sys.path

    for dir in search_path:
        if not isinstance(dir, str):
            continue

        finder = get_importer(dir)
        if finder is not None:
            portions = []
            if hasattr(finder, 'find_spec'):
                spec = finder.find_spec(final_name)
                if spec is not None:
                    portions = spec.submodule_search_locations or []
            # Is this finder PEP 420 compliant?
            elif hasattr(finder, 'find_loader'):
                _, portions = finder.find_loader(final_name)

            for portion in portions:
                # XXX This may still add duplicate entries to path on
                # case-insensitive filesystems
                if portion not in path:
                    path.append(portion)

        # XXX Is this the right thing for subpackages like zope.app?
        # It looks for a file named "zope.app.pkg"
        pkgfile = os.path.join(dir, sname_pkg)
        if os.path.isfile(pkgfile):
            try:
                f = open(pkgfile)
            except OSError as msg:
                sys.stderr.write("Can't open %s: %s\n" %
                                 (pkgfile, msg))
            else:
                with f:
                    for line in f:
                        line = line.rstrip('\n')
                        if not line or line.startswith('#'):
                            continue
                        path.append(line) # Don't check for existence!

    return path