def copyfile(src, dst, *, follow_symlinks=True):
    """Copy data from src to dst in the most efficient way possible.

    If follow_symlinks is not set and src is a symbolic link, a new
    symlink will be created instead of copying the file it points to.

    """
    sys.audit("shutil.copyfile", src, dst)

    if _samefile(src, dst):
        raise SameFileError("{!r} and {!r} are the same file".format(src, dst))

    file_size = 0
    for i, fn in enumerate([src, dst]):
        try:
            st = _stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if stat.S_ISFIFO(st.st_mode):
                fn = fn.path if isinstance(fn, os.DirEntry) else fn
                raise SpecialFileError("`%s` is a named pipe" % fn)
            if _WINDOWS and i == 0:
                file_size = st.st_size

    if not follow_symlinks and _islink(src):
        os.symlink(os.readlink(src), dst)
    else:
        with open(src, 'rb') as fsrc:
            try:
                with open(dst, 'wb') as fdst:
                    # macOS
                    if _HAS_FCOPYFILE:
                        try:
                            _fastcopy_fcopyfile(fsrc, fdst, posix._COPYFILE_DATA)
                            return dst
                        except _GiveupOnFastCopy:
                            pass
                    # Linux / Android / Solaris
                    elif _USE_CP_SENDFILE or _USE_CP_COPY_FILE_RANGE:
                        # reflink may be implicit in copy_file_range.
                        if _USE_CP_COPY_FILE_RANGE:
                            try:
                                _fastcopy_copy_file_range(fsrc, fdst)
                                return dst
                            except _GiveupOnFastCopy:
                                pass
                        if _USE_CP_SENDFILE:
                            try:
                                _fastcopy_sendfile(fsrc, fdst)
                                return dst
                            except _GiveupOnFastCopy:
                                pass
                    # Windows, see:
                    # https://github.com/python/cpython/pull/7160#discussion_r195405230
                    elif _WINDOWS and file_size > 0:
                        _copyfileobj_readinto(fsrc, fdst, min(file_size, COPY_BUFSIZE))
                        return dst

                    copyfileobj(fsrc, fdst)

            # Issue 43219, raise a less confusing exception
            except IsADirectoryError as e:
                if not os.path.exists(dst):
                    raise FileNotFoundError(f'Directory does not exist: {dst}') from e
                else:
                    raise

    return dst