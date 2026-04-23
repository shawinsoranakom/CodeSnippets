def __init__(self, filename, mode, block=True, encoding=None):
        if mode not in {'r', 'rb', 'a', 'ab', 'w', 'wb'}:
            raise NotImplementedError(mode)
        self.mode, self.block = mode, block

        writable = any(f in mode for f in 'wax+')
        readable = any(f in mode for f in 'r+')
        flags = functools.reduce(operator.ior, (
            getattr(os, 'O_CLOEXEC', 0),  # UNIX only
            getattr(os, 'O_BINARY', 0),  # Windows only
            getattr(os, 'O_NOINHERIT', 0),  # Windows only
            os.O_CREAT if writable else 0,  # O_TRUNC only after locking
            os.O_APPEND if 'a' in mode else 0,
            os.O_EXCL if 'x' in mode else 0,
            os.O_RDONLY if not writable else os.O_RDWR if readable else os.O_WRONLY,
        ))

        self.f = os.fdopen(os.open(filename, flags, 0o666), mode, encoding=encoding)