def _read_directory(archive):
    try:
        fp = _io.open_code(archive)
    except OSError:
        raise ZipImportError(f"can't open Zip file: {archive!r}", path=archive)

    with fp:
        # GH-87235: On macOS all file descriptors for /dev/fd/N share the same
        # file offset, reset the file offset after scanning the zipfile directory
        # to not cause problems when some runs 'python3 /dev/fd/9 9<some_script'
        start_offset = fp.tell()
        try:
            # Check if there's a comment.
            try:
                fp.seek(0, 2)
                file_size = fp.tell()
            except OSError:
                raise ZipImportError(f"can't read Zip file: {archive!r}",
                                     path=archive)
            max_comment_plus_dirs_size = (
                MAX_COMMENT_LEN + END_CENTRAL_DIR_SIZE +
                END_CENTRAL_DIR_SIZE_64 + END_CENTRAL_DIR_LOCATOR_SIZE_64)
            max_comment_start = max(file_size - max_comment_plus_dirs_size, 0)
            try:
                fp.seek(max_comment_start)
                data = fp.read(max_comment_plus_dirs_size)
            except OSError:
                raise ZipImportError(f"can't read Zip file: {archive!r}",
                                     path=archive)
            pos = data.rfind(STRING_END_ARCHIVE)
            pos64 = data.rfind(STRING_END_ZIP_64)

            if (pos64 >= 0 and pos64+END_CENTRAL_DIR_SIZE_64+END_CENTRAL_DIR_LOCATOR_SIZE_64==pos):
                # Zip64 at "correct" offset from standard EOCD
                buffer = data[pos64:pos64 + END_CENTRAL_DIR_SIZE_64]
                if len(buffer) != END_CENTRAL_DIR_SIZE_64:
                    raise ZipImportError(
                        f"corrupt Zip64 file: Expected {END_CENTRAL_DIR_SIZE_64} byte "
                        f"zip64 central directory, but read {len(buffer)} bytes.",
                        path=archive)
                header_position = file_size - len(data) + pos64

                central_directory_size = _unpack_uint64(buffer[40:48])
                central_directory_position = _unpack_uint64(buffer[48:56])
                num_entries = _unpack_uint64(buffer[24:32])
            elif pos >= 0:
                buffer = data[pos:pos+END_CENTRAL_DIR_SIZE]
                if len(buffer) != END_CENTRAL_DIR_SIZE:
                    raise ZipImportError(f"corrupt Zip file: {archive!r}",
                                         path=archive)

                header_position = file_size - len(data) + pos

                # Buffer now contains a valid EOCD, and header_position gives the
                # starting position of it.
                central_directory_size = _unpack_uint32(buffer[12:16])
                central_directory_position = _unpack_uint32(buffer[16:20])
                num_entries = _unpack_uint16(buffer[8:10])

                # N.b. if someday you want to prefer the standard (non-zip64) EOCD,
                # you need to adjust position by 76 for arc to be 0.
            else:
                raise ZipImportError(f'not a Zip file: {archive!r}',
                                     path=archive)

            # Buffer now contains a valid EOCD, and header_position gives the
            # starting position of it.
            # XXX: These are cursory checks but are not as exact or strict as they
            # could be.  Checking the arc-adjusted value is probably good too.
            if header_position < central_directory_size:
                raise ZipImportError(f'bad central directory size: {archive!r}', path=archive)
            if header_position < central_directory_position:
                raise ZipImportError(f'bad central directory offset: {archive!r}', path=archive)
            header_position -= central_directory_size
            # On just-a-zipfile these values are the same and arc_offset is zero; if
            # the file has some bytes prepended, `arc_offset` is the number of such
            # bytes.  This is used for pex as well as self-extracting .exe.
            arc_offset = header_position - central_directory_position
            if arc_offset < 0:
                raise ZipImportError(f'bad central directory size or offset: {archive!r}', path=archive)

            files = {}
            # Start of Central Directory
            count = 0
            try:
                fp.seek(header_position)
            except OSError:
                raise ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
            while True:
                buffer = fp.read(46)
                if len(buffer) < 4:
                    raise EOFError('EOF read where not expected')
                # Start of file header
                if buffer[:4] != b'PK\x01\x02':
                    if count != num_entries:
                        raise ZipImportError(
                            f"mismatched num_entries: {count} should be {num_entries} in {archive!r}",
                            path=archive,
                        )
                    break                                # Bad: Central Dir File Header
                if len(buffer) != 46:
                    raise EOFError('EOF read where not expected')
                flags = _unpack_uint16(buffer[8:10])
                compress = _unpack_uint16(buffer[10:12])
                time = _unpack_uint16(buffer[12:14])
                date = _unpack_uint16(buffer[14:16])
                crc = _unpack_uint32(buffer[16:20])
                data_size = _unpack_uint32(buffer[20:24])
                file_size = _unpack_uint32(buffer[24:28])
                name_size = _unpack_uint16(buffer[28:30])
                extra_size = _unpack_uint16(buffer[30:32])
                comment_size = _unpack_uint16(buffer[32:34])
                file_offset = _unpack_uint32(buffer[42:46])
                header_size = name_size + extra_size + comment_size

                try:
                    name = fp.read(name_size)
                except OSError:
                    raise ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
                if len(name) != name_size:
                    raise ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
                # On Windows, calling fseek to skip over the fields we don't use is
                # slower than reading the data because fseek flushes stdio's
                # internal buffers.    See issue #8745.
                try:
                    extra_data_len = header_size - name_size
                    extra_data = memoryview(fp.read(extra_data_len))

                    if len(extra_data) != extra_data_len:
                        raise ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
                except OSError:
                    raise ZipImportError(f"can't read Zip file: {archive!r}", path=archive)

                if flags & 0x800:
                    # UTF-8 file names extension
                    name = name.decode()
                else:
                    # Historical ZIP filename encoding
                    try:
                        name = name.decode('ascii')
                    except UnicodeDecodeError:
                        name = name.decode('latin1').translate(cp437_table)

                name = name.replace('/', path_sep)
                path = _bootstrap_external._path_join(archive, name)

                # Ordering matches unpacking below.
                if (
                    file_size == MAX_UINT32 or
                    data_size == MAX_UINT32 or
                    file_offset == MAX_UINT32
                ):
                    # need to decode extra_data looking for a zip64 extra (which might not
                    # be present)
                    while extra_data:
                        if len(extra_data) < 4:
                            raise ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                        tag = _unpack_uint16(extra_data[:2])
                        size = _unpack_uint16(extra_data[2:4])
                        if len(extra_data) < 4 + size:
                            raise ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                        if tag == ZIP64_EXTRA_TAG:
                            if (len(extra_data) - 4) % 8 != 0:
                                raise ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                            num_extra_values = (len(extra_data) - 4) // 8
                            if num_extra_values > 3:
                                raise ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                            import struct
                            values = list(struct.unpack_from(f"<{min(num_extra_values, 3)}Q",
                                                             extra_data, offset=4))

                            # N.b. Here be dragons: the ordering of these is different than
                            # the header fields, and it's really easy to get it wrong since
                            # naturally-occurring zips that use all 3 are >4GB
                            if file_size == MAX_UINT32:
                                file_size = values.pop(0)
                            if data_size == MAX_UINT32:
                                data_size = values.pop(0)
                            if file_offset == MAX_UINT32:
                                file_offset = values.pop(0)

                            break

                        # For a typical zip, this bytes-slicing only happens 2-3 times, on
                        # small data like timestamps and filesizes.
                        extra_data = extra_data[4+size:]
                    else:
                        _bootstrap._verbose_message(
                            "zipimport: suspected zip64 but no zip64 extra for {!r}",
                            path,
                        )
                # XXX These two statements seem swapped because `central_directory_position`
                # is a position within the actual file, but `file_offset` (when compared) is
                # as encoded in the entry, not adjusted for this file.
                # N.b. this must be after we've potentially read the zip64 extra which can
                # change `file_offset`.
                if file_offset > central_directory_position:
                    raise ZipImportError(f'bad local header offset: {archive!r}', path=archive)
                file_offset += arc_offset

                t = (path, compress, data_size, file_size, file_offset, time, date, crc)
                files[name] = t
                count += 1
        finally:
            fp.seek(start_offset)
    _bootstrap._verbose_message('zipimport: found {} names in {!r}', count, archive)

    # Add implicit directories.
    count = 0
    for name in list(files):
        while True:
            i = name.rstrip(path_sep).rfind(path_sep)
            if i < 0:
                break
            name = name[:i + 1]
            if name in files:
                break
            files[name] = None
            count += 1
    if count:
        _bootstrap._verbose_message('zipimport: added {} implicit directories in {!r}',
                                    count, archive)
    return files