def _iter_filenames(filenames, process, relroot):
    if process is None:
        yield from fsutil.process_filenames(filenames, relroot=relroot)
        return

    onempty = Exception('no filenames provided')
    items = process(filenames, relroot=relroot)
    items, peeked = iterutil.peek_and_iter(items)
    if not items:
        raise onempty
    if isinstance(peeked, str):
        if relroot and relroot is not fsutil.USE_CWD:
            relroot = os.path.abspath(relroot)
        check = (lambda: True)
        for filename, ismany in iterutil.iter_many(items, onempty):
            relfile = fsutil.format_filename(filename, relroot, fixroot=False)
            yield filename, relfile, check, ismany
    elif len(peeked) == 4:
        yield from items
    else:
        raise NotImplementedError