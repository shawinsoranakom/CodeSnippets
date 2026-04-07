def compression_formats(self):
        """A dict mapping format names to (open function, mode arg) tuples."""
        # Forcing binary mode may be revisited after dropping Python 2 support
        # (see #22399).
        compression_formats = {
            None: (open, "rb"),
            "gz": (gzip.GzipFile, "rb"),
            "zip": (SingleZipReader, "r"),
            "stdin": (lambda *args: sys.stdin, None),
        }
        if has_bz2:
            compression_formats["bz2"] = (bz2.BZ2File, "r")
        if has_lzma:
            compression_formats["lzma"] = (lzma.LZMAFile, "r")
            compression_formats["xz"] = (lzma.LZMAFile, "r")
        return compression_formats