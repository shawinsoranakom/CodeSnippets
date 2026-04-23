def __init__(self, files=None, inplace=False, backup="", *,
                 mode="r", openhook=None, encoding=None, errors=None):
        if isinstance(files, str):
            files = (files,)
        elif isinstance(files, os.PathLike):
            files = (os.fspath(files), )
        else:
            if files is None:
                files = sys.argv[1:]
            if not files:
                files = ('-',)
            else:
                files = tuple(files)
        self._files = files
        self._inplace = inplace
        self._backup = backup
        self._savestdout = None
        self._output = None
        self._filename = None
        self._startlineno = 0
        self._filelineno = 0
        self._file = None
        self._isstdin = False
        self._backupfilename = None
        self._encoding = encoding
        self._errors = errors

        # We can not use io.text_encoding() here because old openhook doesn't
        # take encoding parameter.
        if (sys.flags.warn_default_encoding and
                "b" not in mode and encoding is None and openhook is None):
            import warnings
            warnings.warn("'encoding' argument not specified.",
                          EncodingWarning, 2)

        # restrict mode argument to reading modes
        if mode not in ('r', 'rb'):
            raise ValueError("FileInput opening mode must be 'r' or 'rb'")
        self._mode = mode
        self._write_mode = mode.replace('r', 'w')
        if openhook:
            if inplace:
                raise ValueError("FileInput cannot use an opening hook in inplace mode")
            if not callable(openhook):
                raise ValueError("FileInput openhook must be callable")
        self._openhook = openhook