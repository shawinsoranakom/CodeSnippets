def make_archive(base_name, format, root_dir=None, base_dir=None, verbose=0,
                 dry_run=0, owner=None, group=None, logger=None):
    """Create an archive file (eg. zip or tar).

    'base_name' is the name of the file to create, minus any format-specific
    extension; 'format' is the archive format: one of "zip", "tar", "gztar",
    "bztar", "xztar", or "zstdtar".  Or any other registered format.

    'root_dir' is a directory that will be the root directory of the
    archive; ie. we typically chdir into 'root_dir' before creating the
    archive.  'base_dir' is the directory where we start archiving from;
    ie. 'base_dir' will be the common prefix of all files and
    directories in the archive.  'root_dir' and 'base_dir' both default
    to the current directory.  Returns the name of the archive file.

    'owner' and 'group' are used when creating a tar archive. By default,
    uses the current owner and group.
    """
    sys.audit("shutil.make_archive", base_name, format, root_dir, base_dir)
    try:
        format_info = _ARCHIVE_FORMATS[format]
    except KeyError:
        raise ValueError("unknown archive format '%s'" % format) from None

    kwargs = {'dry_run': dry_run, 'logger': logger,
              'owner': owner, 'group': group}

    func = format_info[0]
    for arg, val in format_info[1]:
        kwargs[arg] = val

    base_name = os.fspath(base_name)

    if base_dir is None:
        base_dir = os.curdir
    else:
        base_dir = os.fspath(base_dir)

    supports_root_dir = getattr(func, 'supports_root_dir', False)
    save_cwd = None
    if root_dir is not None:
        root_dir = os.fspath(root_dir)
        stmd = os.stat(root_dir).st_mode
        if not stat.S_ISDIR(stmd):
            raise NotADirectoryError(errno.ENOTDIR, 'Not a directory', root_dir)

        if supports_root_dir:
            kwargs['root_dir'] = root_dir
        else:
            save_cwd = os.getcwd()
            if logger is not None:
                logger.debug("changing into '%s'", root_dir)
            base_name = os.path.abspath(base_name)
            if not dry_run:
                os.chdir(root_dir)

    try:
        filename = func(base_name, base_dir, **kwargs)
    finally:
        if save_cwd is not None:
            if logger is not None:
                logger.debug("changing back to '%s'", save_cwd)
            os.chdir(save_cwd)

    return filename