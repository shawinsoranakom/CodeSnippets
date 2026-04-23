def _get_data(archive, toc_entry):
    datapath, compress, data_size, file_size, file_offset, time, date, crc = toc_entry
    if data_size < 0:
        raise ZipImportError('negative data size')

    with _io.open_code(archive) as fp:
        # Check to make sure the local file header is correct
        try:
            fp.seek(file_offset)
        except OSError:
            raise ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
        buffer = fp.read(30)
        if len(buffer) != 30:
            raise EOFError('EOF read where not expected')

        if buffer[:4] != b'PK\x03\x04':
            # Bad: Local File Header
            raise ZipImportError(f'bad local file header: {archive!r}', path=archive)

        name_size = _unpack_uint16(buffer[26:28])
        extra_size = _unpack_uint16(buffer[28:30])
        header_size = 30 + name_size + extra_size
        file_offset += header_size  # Start of file data
        try:
            fp.seek(file_offset)
        except OSError:
            raise ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
        raw_data = fp.read(data_size)
        if len(raw_data) != data_size:
            raise OSError("zipimport: can't read data")

    match compress:
        case 0:  # stored
            return raw_data
        case 8:  # deflate aka zlib
            try:
                decompress = _get_zlib_decompress_func()
            except Exception:
                raise ZipImportError("can't decompress data; zlib not available")
            return decompress(raw_data, -15)
        case 93:  # zstd
            try:
                return _zstd_decompress(raw_data)
            except Exception:
                raise ZipImportError("could not decompress zstd data")
        # bz2 and lzma could be added, but are largely obsolete.
        case _:
            raise ZipImportError(f"zipimport: unsupported compression {compress}")