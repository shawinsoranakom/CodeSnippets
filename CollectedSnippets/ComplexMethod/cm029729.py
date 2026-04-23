def _read_gzip_header(fp):
    '''Read a gzip header from `fp` and progress to the end of the header.

    Returns last mtime if header was present or None otherwise.
    '''
    magic = fp.read(2)
    if magic == b'':
        return None

    if magic != b'\037\213':
        raise BadGzipFile('Not a gzipped file (%r)' % magic)

    (method, flag, last_mtime) = struct.unpack("<BBIxx", _read_exact(fp, 8))
    if method != 8:
        raise BadGzipFile('Unknown compression method')

    if flag & FEXTRA:
        # Read & discard the extra field, if present
        extra_len, = struct.unpack("<H", _read_exact(fp, 2))
        _read_exact(fp, extra_len)
    if flag & FNAME:
        # Read and discard a null-terminated string containing the filename
        while True:
            s = fp.read(1)
            if not s or s==b'\000':
                break
    if flag & FCOMMENT:
        # Read and discard a null-terminated string containing a comment
        while True:
            s = fp.read(1)
            if not s or s==b'\000':
                break
    if flag & FHCRC:
        _read_exact(fp, 2)     # Read & discard the 16-bit header CRC
    return last_mtime