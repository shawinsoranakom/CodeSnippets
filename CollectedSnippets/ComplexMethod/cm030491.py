def __init__(self, file, /, mode='r', *,
                 level=None, options=None, zstd_dict=None):
        """Open a Zstandard compressed file in binary mode.

        *file* can be either an file-like object, or a file name to open.

        *mode* can be 'r' for reading (default), 'w' for (over)writing, 'x' for
        creating exclusively, or 'a' for appending. These can equivalently be
        given as 'rb', 'wb', 'xb' and 'ab' respectively.

        *level* is an optional int specifying the compression level to use,
        or COMPRESSION_LEVEL_DEFAULT if not given.

        *options* is an optional dict for advanced compression parameters.
        See CompressionParameter and DecompressionParameter for the possible
        options.

        *zstd_dict* is an optional ZstdDict object, a pre-trained Zstandard
        dictionary. See train_dict() to train ZstdDict on sample data.
        """
        self._fp = None
        self._close_fp = False
        self._mode = _MODE_CLOSED
        self._buffer = None

        if not isinstance(mode, str):
            raise ValueError('mode must be a str')
        if options is not None and not isinstance(options, dict):
            raise TypeError('options must be a dict or None')
        mode = mode.removesuffix('b')  # handle rb, wb, xb, ab
        if mode == 'r':
            if level is not None:
                raise TypeError('level is illegal in read mode')
            self._mode = _MODE_READ
        elif mode in {'w', 'a', 'x'}:
            if level is not None and not isinstance(level, int):
                raise TypeError('level must be int or None')
            self._mode = _MODE_WRITE
            self._compressor = ZstdCompressor(level=level, options=options,
                                              zstd_dict=zstd_dict)
            self._pos = 0
        else:
            raise ValueError(f'Invalid mode: {mode!r}')

        if isinstance(file, (str, bytes, PathLike)):
            self._fp = io.open(file, f'{mode}b')
            self._close_fp = True
        elif ((mode == 'r' and hasattr(file, 'read'))
                or (mode != 'r' and hasattr(file, 'write'))):
            self._fp = file
        else:
            raise TypeError('file must be a file-like object '
                            'or a str, bytes, or PathLike object')

        if self._mode == _MODE_READ:
            raw = _streams.DecompressReader(
                self._fp,
                ZstdDecompressor,
                zstd_dict=zstd_dict,
                options=options,
            )
            self._buffer = io.BufferedReader(raw)