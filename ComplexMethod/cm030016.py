def __init__(self, name, mode, comptype, fileobj, bufsize,
                 compresslevel, preset):
        """Construct a _Stream object.
        """
        self._extfileobj = True
        if fileobj is None:
            fileobj = _LowLevelFile(name, mode)
            self._extfileobj = False

        if comptype == '*':
            # Enable transparent compression detection for the
            # stream interface
            fileobj = _StreamProxy(fileobj)
            comptype = fileobj.getcomptype()

        self.name     = os.fspath(name) if name is not None else ""
        self.mode     = mode
        self.comptype = comptype
        self.fileobj  = fileobj
        self.bufsize  = bufsize
        self.buf      = b""
        self.pos      = 0
        self.closed   = False

        try:
            if comptype == "gz":
                try:
                    import zlib
                except ImportError:
                    raise CompressionError("zlib module is not available") from None
                self.zlib = zlib
                self.crc = zlib.crc32(b"")
                if mode == "r":
                    self.exception = zlib.error
                    self._init_read_gz()
                else:
                    self._init_write_gz(compresslevel)

            elif comptype == "bz2":
                try:
                    import bz2
                except ImportError:
                    raise CompressionError("bz2 module is not available") from None
                if mode == "r":
                    self.dbuf = b""
                    self.cmp = bz2.BZ2Decompressor()
                    self.exception = OSError
                else:
                    self.cmp = bz2.BZ2Compressor(compresslevel)

            elif comptype == "xz":
                try:
                    import lzma
                except ImportError:
                    raise CompressionError("lzma module is not available") from None
                if mode == "r":
                    self.dbuf = b""
                    self.cmp = lzma.LZMADecompressor()
                    self.exception = lzma.LZMAError
                else:
                    self.cmp = lzma.LZMACompressor(preset=preset)
            elif comptype == "zst":
                try:
                    from compression import zstd
                except ImportError:
                    raise CompressionError("compression.zstd module is not available") from None
                if mode == "r":
                    self.dbuf = b""
                    self.cmp = zstd.ZstdDecompressor()
                    self.exception = zstd.ZstdError
                else:
                    self.cmp = zstd.ZstdCompressor()
            elif comptype != "tar":
                raise CompressionError("unknown compression type %r" % comptype)

        except:
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
            raise