def __init__(self, name=None, mode="r", fileobj=None, format=None,
            tarinfo=None, dereference=None, ignore_zeros=None, encoding=None,
            errors="surrogateescape", pax_headers=None, debug=None,
            errorlevel=None, copybufsize=None, stream=False):
        """Open an (uncompressed) tar archive 'name'. 'mode' is either 'r' to
           read from an existing archive, 'a' to append data to an existing
           file or 'w' to create a new file overwriting an existing one. 'mode'
           defaults to 'r'.
           If 'fileobj' is given, it is used for reading or writing data. If it
           can be determined, 'mode' is overridden by 'fileobj's mode.
           'fileobj' is not closed, when TarFile is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb", "x": "xb"}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a', 'w' or 'x'")
        self.mode = mode
        self._mode = modes[mode]

        if not fileobj:
            if self.mode == "a" and not os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if (name is None and hasattr(fileobj, "name") and
                isinstance(fileobj.name, (str, bytes))):
                name = fileobj.name
            if hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj

        self.stream = stream

        # Init attributes.
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding
        self.errors = errors

        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}

        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel

        # Init datastructures.
        self.copybufsize = copybufsize
        self.closed = False
        self.members = []       # list of members as TarInfo objects
        self._loaded = False    # flag if all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added
        self._unames = {}       # Cached mappings of uid -> uname
        self._gnames = {}       # Cached mappings of gid -> gname

        try:
            if self.mode == "r":
                self.firstmember = None
                self.firstmember = self.next()

            if self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                while True:
                    self.fileobj.seek(self.offset)
                    try:
                        tarinfo = self.tarinfo.fromtarfile(self)
                        self.members.append(tarinfo)
                    except EOFHeaderError:
                        self.fileobj.seek(self.offset)
                        break
                    except HeaderError as e:
                        raise ReadError(str(e)) from None

            if self.mode in ("a", "w", "x"):
                self._loaded = True

                if self.pax_headers:
                    buf = self.tarinfo.create_pax_global_header(self.pax_headers.copy())
                    self.fileobj.write(buf)
                    self.offset += len(buf)
        except:
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
            raise