def _check_compression(compression):
    if compression == ZIP_STORED:
        pass
    elif compression == ZIP_DEFLATED:
        if not zlib:
            raise RuntimeError(
                "Compression requires the (missing) zlib module")
    elif compression == ZIP_BZIP2:
        if not bz2:
            raise RuntimeError(
                "Compression requires the (missing) bz2 module")
    elif compression == ZIP_LZMA:
        if not lzma:
            raise RuntimeError(
                "Compression requires the (missing) lzma module")
    elif compression == ZIP_ZSTANDARD:
        if not zstd:
            raise RuntimeError(
                "Compression requires the (missing) compression.zstd module")
    else:
        raise NotImplementedError("That compression method is not supported")