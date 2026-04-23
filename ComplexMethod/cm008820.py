def sanitize_open(filename, open_mode):
    """Try to open the given filename, and slightly tweak it if this fails.

    Attempts to open the given filename. If this fails, it tries to change
    the filename slightly, step by step, until it's either able to open it
    or it fails and raises a final exception, like the standard open()
    function.

    It returns the tuple (stream, definitive_file_name).
    """
    if filename == '-':
        if sys.platform == 'win32':
            import msvcrt

            # stdout may be any IO stream, e.g. when using contextlib.redirect_stdout
            with contextlib.suppress(io.UnsupportedOperation):
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        return (sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout, filename)

    for attempt in range(2):
        try:
            try:
                if sys.platform == 'win32':
                    # FIXME: An exclusive lock also locks the file from being read.
                    # Since windows locks are mandatory, don't lock the file on windows (for now).
                    # Ref: https://github.com/yt-dlp/yt-dlp/issues/3124
                    raise LockingUnsupportedError
                stream = locked_file(filename, open_mode, block=False).__enter__()
            except OSError:
                stream = open(filename, open_mode)
            return stream, filename
        except OSError as err:
            if attempt or err.errno in (errno.EACCES,):
                raise
            old_filename, filename = filename, sanitize_path(filename)
            if old_filename == filename:
                raise