def __init__(self, filename, mode="r", *, compresslevel=9):
        """Open a bzip2-compressed file.

        If filename is a str, bytes, or PathLike object, it gives the
        name of the file to be opened. Otherwise, it should be a file
        object, which will be used to read or write the compressed data.

        mode can be 'r' for reading (default), 'w' for (over)writing,
        'x' for creating exclusively, or 'a' for appending. These can
        equivalently be given as 'rb', 'wb', 'xb', and 'ab'.

        If mode is 'w', 'x' or 'a', compresslevel can be a number between 1
        and 9 specifying the level of compression: 1 produces the least
        compression, and 9 (default) produces the most compression.

        If mode is 'r', the input file may be the concatenation of
        multiple compressed streams.
        """
        self._fp = None
        self._closefp = False
        self._mode = None

        if not (1 <= compresslevel <= 9):
            raise ValueError("compresslevel must be between 1 and 9")

        if mode in ("", "r", "rb"):
            mode = "rb"
            mode_code = _MODE_READ
        elif mode in ("w", "wb"):
            mode = "wb"
            mode_code = _MODE_WRITE
            self._compressor = BZ2Compressor(compresslevel)
        elif mode in ("x", "xb"):
            mode = "xb"
            mode_code = _MODE_WRITE
            self._compressor = BZ2Compressor(compresslevel)
        elif mode in ("a", "ab"):
            mode = "ab"
            mode_code = _MODE_WRITE
            self._compressor = BZ2Compressor(compresslevel)
        else:
            raise ValueError("Invalid mode: %r" % (mode,))

        if isinstance(filename, (str, bytes, os.PathLike)):
            self._fp = _builtin_open(filename, mode)
            self._closefp = True
            self._mode = mode_code
        elif hasattr(filename, "read") or hasattr(filename, "write"):
            self._fp = filename
            self._mode = mode_code
        else:
            raise TypeError("filename must be a str, bytes, file or PathLike object")

        if self._mode == _MODE_READ:
            raw = _streams.DecompressReader(self._fp,
                BZ2Decompressor, trailing_error=OSError)
            self._buffer = io.BufferedReader(raw)
        else:
            self._pos = 0