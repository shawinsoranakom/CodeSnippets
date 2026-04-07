def decompress(gzipped_string):
        # Use zlib to ensure gzipped_string contains exactly one gzip stream.
        return zlib.decompress(gzipped_string, zlib.MAX_WBITS | 16)