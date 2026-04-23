def _unmarshal_code(self, pathname, fullpath, fullname, data):
    exc_details = {
        'name': fullname,
        'path': fullpath,
    }

    flags = _bootstrap_external._classify_pyc(data, fullname, exc_details)

    hash_based = flags & 0b1 != 0
    if hash_based:
        check_source = flags & 0b10 != 0
        if (_imp.check_hash_based_pycs != 'never' and
                (check_source or _imp.check_hash_based_pycs == 'always')):
            source_bytes = _get_pyc_source(self, fullpath)
            if source_bytes is not None:
                source_hash = _imp.source_hash(
                    _imp.pyc_magic_number_token,
                    source_bytes,
                )

                _bootstrap_external._validate_hash_pyc(
                    data, source_hash, fullname, exc_details)
    else:
        source_mtime, source_size = \
            _get_mtime_and_size_of_source(self, fullpath)

        if source_mtime:
            # We don't use _bootstrap_external._validate_timestamp_pyc
            # to allow for a more lenient timestamp check.
            if (not _eq_mtime(_unpack_uint32(data[8:12]), source_mtime) or
                    _unpack_uint32(data[12:16]) != source_size):
                _bootstrap._verbose_message(
                    f'bytecode is stale for {fullname!r}')
                return None

    code = marshal.loads(data[16:])
    if not isinstance(code, _code_type):
        raise TypeError(f'compiled module {pathname!r} is not a code object')
    return code