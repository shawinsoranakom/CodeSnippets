def open(cls, name=None, mode="r", fileobj=None, bufsize=RECORDSIZE, **kwargs):
        """Open a tar archive for reading, writing or appending. Return
           an appropriate TarFile class.

           mode:
           'r' or 'r:*' open for reading with transparent compression
           'r:'         open for reading exclusively uncompressed
           'r:gz'       open for reading with gzip compression
           'r:bz2'      open for reading with bzip2 compression
           'r:xz'       open for reading with lzma compression
           'r:zst'      open for reading with zstd compression
           'a' or 'a:'  open for appending, creating the file if necessary
           'w' or 'w:'  open for writing without compression
           'w:gz'       open for writing with gzip compression
           'w:bz2'      open for writing with bzip2 compression
           'w:xz'       open for writing with lzma compression
           'w:zst'      open for writing with zstd compression

           'x' or 'x:'  create a tarfile exclusively without compression, raise
                        an exception if the file is already created
           'x:gz'       create a gzip compressed tarfile, raise an exception
                        if the file is already created
           'x:bz2'      create a bzip2 compressed tarfile, raise an exception
                        if the file is already created
           'x:xz'       create an lzma compressed tarfile, raise an exception
                        if the file is already created
           'x:zst'      create a zstd compressed tarfile, raise an exception
                        if the file is already created

           'r|*'        open a stream of tar blocks with transparent compression
           'r|'         open an uncompressed stream of tar blocks for reading
           'r|gz'       open a gzip compressed stream of tar blocks
           'r|bz2'      open a bzip2 compressed stream of tar blocks
           'r|xz'       open an lzma compressed stream of tar blocks
           'r|zst'      open a zstd compressed stream of tar blocks
           'w|'         open an uncompressed stream for writing
           'w|gz'       open a gzip compressed stream for writing
           'w|bz2'      open a bzip2 compressed stream for writing
           'w|xz'       open an lzma compressed stream for writing
           'w|zst'      open a zstd compressed stream for writing
        """

        if not name and not fileobj:
            raise ValueError("nothing to open")

        if mode in ("r", "r:*"):
            # Find out which *open() is appropriate for opening the file.
            def not_compressed(comptype):
                return cls.OPEN_METH[comptype] == 'taropen'
            error_msgs = []
            for comptype in sorted(cls.OPEN_METH, key=not_compressed):
                func = getattr(cls, cls.OPEN_METH[comptype])
                if fileobj is not None:
                    saved_pos = fileobj.tell()
                try:
                    return func(name, "r", fileobj, **kwargs)
                except (ReadError, CompressionError) as e:
                    error_msgs.append(f'- method {comptype}: {e!r}')
                    if fileobj is not None:
                        fileobj.seek(saved_pos)
                    continue
            error_msgs_summary = '\n'.join(error_msgs)
            raise ReadError(f"file could not be opened successfully:\n{error_msgs_summary}")

        elif ":" in mode:
            filemode, comptype = mode.split(":", 1)
            filemode = filemode or "r"
            comptype = comptype or "tar"

            # Select the *open() function according to
            # given compression.
            if comptype in cls.OPEN_METH:
                func = getattr(cls, cls.OPEN_METH[comptype])
            else:
                raise CompressionError("unknown compression type %r" % comptype)
            return func(name, filemode, fileobj, **kwargs)

        elif "|" in mode:
            filemode, comptype = mode.split("|", 1)
            filemode = filemode or "r"
            comptype = comptype or "tar"

            if filemode not in ("r", "w"):
                raise ValueError("mode must be 'r' or 'w'")
            if "compresslevel" in kwargs and comptype not in ("gz", "bz2"):
                raise ValueError(
                    "compresslevel is only valid for w|gz and w|bz2 modes"
                )
            if "preset" in kwargs and comptype not in ("xz",):
                raise ValueError("preset is only valid for w|xz mode")

            compresslevel = kwargs.pop("compresslevel", 6)
            preset = kwargs.pop("preset", None)
            stream = _Stream(name, filemode, comptype, fileobj, bufsize,
                             compresslevel, preset)
            try:
                t = cls(name, filemode, stream, **kwargs)
            except:
                stream.close()
                raise
            t._extfileobj = False
            return t

        elif mode in ("a", "w", "x"):
            return cls.taropen(name, mode, fileobj, **kwargs)

        raise ValueError("undiscernible mode")