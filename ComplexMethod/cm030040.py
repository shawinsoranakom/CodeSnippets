def create_archive(source, target=None, interpreter=None, main=None,
                   filter=None, compressed=False):
    """Create an application archive from SOURCE.

    The SOURCE can be the name of a directory, or a filename or a file-like
    object referring to an existing archive.

    The content of SOURCE is packed into an application archive in TARGET,
    which can be a filename or a file-like object.  If SOURCE is a directory,
    TARGET can be omitted and will default to the name of SOURCE with .pyz
    appended.

    The created application archive will have a shebang line specifying
    that it should run with INTERPRETER (there will be no shebang line if
    INTERPRETER is None), and a __main__.py which runs MAIN (if MAIN is
    not specified, an existing __main__.py will be used).  It is an error
    to specify MAIN for anything other than a directory source with no
    __main__.py, and it is an error to omit MAIN if the directory has no
    __main__.py.
    """
    # Are we copying an existing archive?
    source_is_file = False
    if hasattr(source, 'read') and hasattr(source, 'readline'):
        source_is_file = True
    else:
        source = pathlib.Path(source)
        if source.is_file():
            source_is_file = True

    if source_is_file:
        _copy_archive(source, target, interpreter)
        return

    # We are creating a new archive from a directory.
    if not source.exists():
        raise ZipAppError("Source does not exist")
    has_main = (source / '__main__.py').is_file()
    if main and has_main:
        raise ZipAppError(
            "Cannot specify entry point if the source has __main__.py")
    if not (main or has_main):
        raise ZipAppError("Archive has no entry point")

    main_py = None
    if main:
        # Check that main has the right format.
        mod, sep, fn = main.partition(':')
        mod_ok = all(part.isidentifier() for part in mod.split('.'))
        fn_ok = all(part.isidentifier() for part in fn.split('.'))
        if not (sep == ':' and mod_ok and fn_ok):
            raise ZipAppError("Invalid entry point: " + main)
        main_py = MAIN_TEMPLATE.format(module=mod, fn=fn)

    if target is None:
        target = source.with_suffix('.pyz')
    elif not hasattr(target, 'write'):
        target = pathlib.Path(target)

    # Create the list of files to add to the archive now, in case
    # the target is being created in the source directory - we
    # don't want the target being added to itself
    files_to_add = {}
    for path in sorted(source.rglob('*')):
        relative_path = path.relative_to(source)
        if filter is None or filter(relative_path):
            files_to_add[path] = relative_path

    # The target cannot be in the list of files to add. If it were, we'd
    # end up overwriting the source file and writing the archive into
    # itself, which is an error. We therefore check for that case and
    # provide a helpful message for the user.

    # Note that we only do a simple path equality check. This won't
    # catch every case, but it will catch the common case where the
    # source is the CWD and the target is a file in the CWD. More
    # thorough checks don't provide enough value to justify the extra
    # cost.

    # If target is a file-like object, it will simply fail to compare
    # equal to any of the entries in files_to_add, so there's no need
    # to add a special check for that.
    if target in files_to_add:
        raise ZipAppError(
            f"The target archive {target} overwrites one of the source files.")

    with _maybe_open(target, 'wb') as fd:
        _write_file_prefix(fd, interpreter)
        compression = (zipfile.ZIP_DEFLATED if compressed else
                       zipfile.ZIP_STORED)
        with zipfile.ZipFile(fd, 'w', compression=compression) as z:
            for path, relative_path in files_to_add.items():
                z.write(path, relative_path.as_posix())
            if main_py:
                z.writestr('__main__.py', main_py.encode('utf-8'))

    if interpreter and not hasattr(target, 'write'):
        target.chmod(target.stat().st_mode | stat.S_IEXEC)