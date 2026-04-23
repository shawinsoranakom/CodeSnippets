def __init__(self, filename=None, mode=None,
                 compresslevel=_COMPRESS_LEVEL_TRADEOFF, fileobj=None, mtime=None):
        """Constructor for the GzipFile class.

        At least one of fileobj and filename must be given a
        non-trivial value.

        The new class instance is based on fileobj, which can be a regular
        file, an io.BytesIO object, or any other object which simulates a file.
        It defaults to None, in which case filename is opened to provide
        a file object.

        When fileobj is not None, the filename argument is only used to be
        included in the gzip file header, which may include the original
        filename of the uncompressed file.  It defaults to the filename of
        fileobj, if discernible; otherwise, it defaults to the empty string,
        and in this case the original filename is not included in the header.

        The mode argument can be any of 'r', 'rb', 'a', 'ab', 'w', 'wb', 'x', or
        'xb' depending on whether the file will be read or written.  The default
        is the mode of fileobj if discernible; otherwise, the default is 'rb'.
        A mode of 'r' is equivalent to one of 'rb', and similarly for 'w' and
        'wb', 'a' and 'ab', and 'x' and 'xb'.

        The compresslevel argument is an integer from 0 to 9 controlling the
        level of compression; 1 is fastest and produces the least compression,
        and 9 is slowest and produces the most compression. 0 is no compression
        at all. The default is 9.

        The optional mtime argument is the timestamp requested by gzip. The time
        is in Unix format, i.e., seconds since 00:00:00 UTC, January 1, 1970.
        If mtime is omitted or None, the current time is used. Use mtime = 0
        to generate a compressed stream that does not depend on creation time.

        """

        # Ensure attributes exist at __del__
        self.mode = None
        self.fileobj = None
        self._buffer = None

        if mode and ('t' in mode or 'U' in mode):
            raise ValueError("Invalid mode: {!r}".format(mode))
        if mode and 'b' not in mode:
            mode += 'b'

        try:
            if fileobj is None:
                fileobj = self.myfileobj = builtins.open(filename, mode or 'rb')
            if filename is None:
                filename = getattr(fileobj, 'name', '')
                if not isinstance(filename, (str, bytes)):
                    filename = ''
            else:
                filename = os.fspath(filename)
            origmode = mode
            if mode is None:
                mode = getattr(fileobj, 'mode', 'rb')


            if mode.startswith('r'):
                self.mode = READ
                raw = _GzipReader(fileobj)
                self._buffer = io.BufferedReader(raw)
                self.name = filename

            elif mode.startswith(('w', 'a', 'x')):
                if origmode is None:
                    import warnings
                    warnings.warn(
                        "GzipFile was opened for writing, but this will "
                        "change in future Python releases.  "
                        "Specify the mode argument for opening it for writing.",
                        FutureWarning, 2)
                self.mode = WRITE
                self._init_write(filename)
                self.compress = zlib.compressobj(compresslevel,
                                                 zlib.DEFLATED,
                                                 -zlib.MAX_WBITS,
                                                 zlib.DEF_MEM_LEVEL,
                                                 0)
                self._write_mtime = mtime
                self._buffer_size = _WRITE_BUFFER_SIZE
                self._buffer = io.BufferedWriter(_WriteBufferStream(self),
                                                 buffer_size=self._buffer_size)
            else:
                raise ValueError("Invalid mode: {!r}".format(mode))

            self.fileobj = fileobj

            if self.mode == WRITE:
                self._write_gzip_header(compresslevel)
        except:
            # Avoid a ResourceWarning if the write fails,
            # eg read-only file or KeyboardInterrupt
            self._close()
            raise