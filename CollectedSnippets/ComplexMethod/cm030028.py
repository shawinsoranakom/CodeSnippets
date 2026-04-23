def gzopen(cls, name, mode="r", fileobj=None, compresslevel=6, **kwargs):
        """Open gzip compressed tar archive name for reading or writing.
           Appending is not allowed.
        """
        if mode not in ("r", "w", "x"):
            raise ValueError("mode must be 'r', 'w' or 'x'")

        try:
            from gzip import GzipFile
        except ImportError:
            raise CompressionError("gzip module is not available") from None

        try:
            fileobj = GzipFile(name, mode + "b", compresslevel, fileobj)
        except OSError as e:
            if fileobj is not None and mode == 'r':
                raise ReadError("not a gzip file") from e
            raise

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except OSError as e:
            fileobj.close()
            if mode == 'r':
                raise ReadError("not a gzip file") from e
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t