def __init__(self, file, mode='r', closefd=True, opener=None):
        """Open a file.  The mode can be 'r' (default), 'w', 'x' or 'a' for reading,
        writing, exclusive creation or appending.  The file will be created if it
        doesn't exist when opened for writing or appending; it will be truncated
        when opened for writing.  A FileExistsError will be raised if it already
        exists when opened for creating. Opening a file for creating implies
        writing so this mode behaves in a similar way to 'w'. Add a '+' to the mode
        to allow simultaneous reading and writing. A custom opener can be used by
        passing a callable as *opener*. The underlying file descriptor for the file
        object is then obtained by calling opener with (*name*, *flags*).
        *opener* must return an open file descriptor (passing os.open as *opener*
        results in functionality similar to passing None).
        """
        if self._fd >= 0:
            # Have to close the existing file first.
            self._stat_atopen = None
            try:
                if self._closefd:
                    os.close(self._fd)
            finally:
                self._fd = -1

        if isinstance(file, float):
            raise TypeError('integer argument expected, got float')
        if isinstance(file, int):
            if isinstance(file, bool):
                import warnings
                warnings.warn("bool is used as a file descriptor",
                              RuntimeWarning, stacklevel=2)
                file = int(file)
            fd = file
            if fd < 0:
                raise ValueError('negative file descriptor')
        else:
            fd = -1

        if not isinstance(mode, str):
            raise TypeError('invalid mode: %s' % (mode,))
        if not set(mode) <= set('xrwab+'):
            raise ValueError('invalid mode: %s' % (mode,))
        if sum(c in 'rwax' for c in mode) != 1 or mode.count('+') > 1:
            raise ValueError('Must have exactly one of create/read/write/append '
                             'mode and at most one plus')

        if 'x' in mode:
            self._created = True
            self._writable = True
            flags = os.O_EXCL | os.O_CREAT
        elif 'r' in mode:
            self._readable = True
            flags = 0
        elif 'w' in mode:
            self._writable = True
            self._truncate = True
            flags = os.O_CREAT | os.O_TRUNC
        elif 'a' in mode:
            self._writable = True
            self._appending = True
            flags = os.O_APPEND | os.O_CREAT

        if '+' in mode:
            self._readable = True
            self._writable = True

        if self._readable and self._writable:
            flags |= os.O_RDWR
        elif self._readable:
            flags |= os.O_RDONLY
        else:
            flags |= os.O_WRONLY

        flags |= getattr(os, 'O_BINARY', 0)

        noinherit_flag = (getattr(os, 'O_NOINHERIT', 0) or
                          getattr(os, 'O_CLOEXEC', 0))
        flags |= noinherit_flag

        owned_fd = None
        try:
            if fd < 0:
                if not closefd:
                    raise ValueError('Cannot use closefd=False with file name')
                if opener is None:
                    fd = os.open(file, flags, 0o666)
                else:
                    fd = opener(file, flags)
                    if not isinstance(fd, int):
                        raise TypeError('expected integer from opener')
                    if fd < 0:
                        # bpo-27066: Raise a ValueError for bad value.
                        raise ValueError(f'opener returned {fd}')
                owned_fd = fd
                if not noinherit_flag:
                    os.set_inheritable(fd, False)

            self._closefd = closefd
            self._stat_atopen = os.fstat(fd)
            try:
                if stat.S_ISDIR(self._stat_atopen.st_mode):
                    raise IsADirectoryError(errno.EISDIR,
                                            os.strerror(errno.EISDIR), file)
            except AttributeError:
                # Ignore the AttributeError if stat.S_ISDIR or errno.EISDIR
                # don't exist.
                pass

            if _setmode:
                # don't translate newlines (\r\n <=> \n)
                _setmode(fd, os.O_BINARY)

            self.name = file
            if self._appending:
                # For consistent behaviour, we explicitly seek to the
                # end of file (otherwise, it might be done only on the
                # first write()).
                try:
                    os.lseek(fd, 0, SEEK_END)
                except OSError as e:
                    if e.errno != errno.ESPIPE:
                        raise
        except:
            self._stat_atopen = None
            if owned_fd is not None:
                os.close(owned_fd)
            raise
        self._fd = fd