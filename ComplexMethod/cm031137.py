def copyfileobj(source_f, target_f):
    """
    Copy data from file-like object source_f to file-like object target_f.
    """
    try:
        source_fd = source_f.fileno()
        target_fd = target_f.fileno()
    except Exception:
        pass  # Fall through to generic code.
    else:
        try:
            # Use OS copy-on-write where available.
            if _ficlone:
                try:
                    _ficlone(source_fd, target_fd)
                    return
                except OSError as err:
                    if err.errno not in (EBADF, EOPNOTSUPP, ETXTBSY, EXDEV):
                        raise err

            # Use OS copy where available.
            if _fcopyfile:
                try:
                    _fcopyfile(source_fd, target_fd)
                    return
                except OSError as err:
                    if err.errno not in (EINVAL, ENOTSUP):
                        raise err
            if _copy_file_range:
                try:
                    _copy_file_range(source_fd, target_fd)
                    return
                except OSError as err:
                    if err.errno not in (ETXTBSY, EXDEV):
                        raise err
            if _sendfile:
                try:
                    _sendfile(source_fd, target_fd)
                    return
                except OSError as err:
                    if err.errno != ENOTSOCK:
                        raise err
        except OSError as err:
            # Produce more useful error messages.
            err.filename = source_f.name
            err.filename2 = target_f.name
            raise err

    # Last resort: copy with fileobj read() and write().
    read_source = source_f.read
    write_target = target_f.write
    while buf := read_source(1024 * 1024):
        write_target(buf)