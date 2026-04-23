def _parse_file(filename, match_kind, get_file_preprocessor, maxsizes):
    srckwargs = {}
    maxsize = _resolve_max_size(filename, maxsizes)
    if maxsize:
        srckwargs['maxtext'], srckwargs['maxlines'] = maxsize

    # Preprocess the file.
    preprocess = get_file_preprocessor(filename)
    preprocessed = preprocess()
    if preprocessed is None:
        return

    # Parse the lines.
    srclines = ((l.file, l.data) for l in preprocessed if l.kind == 'source')
    for item in _parse(srclines, **srckwargs):
        if match_kind is not None and not match_kind(item.kind):
            continue
        if not item.filename:
            raise NotImplementedError(repr(item))
        yield item