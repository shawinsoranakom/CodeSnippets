def NamedTemporaryFile(mode='w+b', buffering=-1, encoding=None,
                       newline=None, suffix=None, prefix=None,
                       dir=None, delete=True, *, errors=None,
                       delete_on_close=True):
    """Create and return a temporary file.
    Arguments:
    'prefix', 'suffix', 'dir' -- as for mkstemp.
    'mode' -- the mode argument to io.open (default "w+b").
    'buffering' -- the buffer size argument to io.open (default -1).
    'encoding' -- the encoding argument to io.open (default None)
    'newline' -- the newline argument to io.open (default None)
    'delete' -- whether the file is automatically deleted (default True).
    'delete_on_close' -- if 'delete', whether the file is deleted on close
       (default True) or otherwise either on context manager exit
       (if context manager was used) or on object finalization. .
    'errors' -- the errors argument to io.open (default None)
    The file is created as mkstemp() would do it.

    Returns an object with a file-like interface; the name of the file
    is accessible as its 'name' attribute.  The file will be automatically
    deleted when it is closed unless the 'delete' argument is set to False.

    On POSIX, NamedTemporaryFiles cannot be automatically deleted if
    the creating process is terminated abruptly with a SIGKILL signal.
    Windows can delete the file even in this case.
    """

    prefix, suffix, dir, output_type = _sanitize_params(prefix, suffix, dir)

    flags = _bin_openflags

    # Setting O_TEMPORARY in the flags causes the OS to delete
    # the file when it is closed.  This is only supported by Windows.
    if _os.name == 'nt' and delete and delete_on_close:
        flags |= _os.O_TEMPORARY

    if "b" not in mode:
        encoding = _io.text_encoding(encoding)

    name = None
    def opener(*args):
        nonlocal name
        fd, name = _mkstemp_inner(dir, prefix, suffix, flags, output_type)
        return fd
    try:
        file = _io.open(dir, mode, buffering=buffering,
                        newline=newline, encoding=encoding, errors=errors,
                        opener=opener)
        try:
            raw = getattr(file, 'buffer', file)
            raw = getattr(raw, 'raw', raw)
            raw.name = name
            return _TemporaryFileWrapper(file, name, delete, delete_on_close)
        except:
            file.close()
            raise
    except:
        if name is not None and not (
            _os.name == 'nt' and delete and delete_on_close):
            _os.unlink(name)
        raise