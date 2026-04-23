def copy2(src, dst, *, follow_symlinks=True):
    """Copy data and metadata. Return the file's destination.

    Metadata is copied with copystat(). Please see the copystat function
    for more information.

    The destination may be a directory.

    If follow_symlinks is false, symlinks won't be followed. This
    resembles GNU's "cp -P src dst".
    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))

    if hasattr(_winapi, "CopyFile2"):
        src_ = os.fsdecode(src)
        dst_ = os.fsdecode(dst)
        flags = _winapi.COPY_FILE_ALLOW_DECRYPTED_DESTINATION # for compat
        if not follow_symlinks:
            flags |= _winapi.COPY_FILE_COPY_SYMLINK
        try:
            _winapi.CopyFile2(src_, dst_, flags)
            return dst
        except OSError as exc:
            if (exc.winerror == _winapi.ERROR_PRIVILEGE_NOT_HELD
                and not follow_symlinks):
                # Likely encountered a symlink we aren't allowed to create.
                # Fall back on the old code
                pass
            elif exc.winerror == _winapi.ERROR_ACCESS_DENIED:
                # Possibly encountered a hidden or readonly file we can't
                # overwrite. Fall back on old code
                pass
            else:
                raise

    copyfile(src, dst, follow_symlinks=follow_symlinks)
    copystat(src, dst, follow_symlinks=follow_symlinks)
    return dst