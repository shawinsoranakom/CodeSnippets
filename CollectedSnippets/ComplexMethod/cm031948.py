def process_filenames(filenames, *,
                      start=None,
                      include=None,
                      exclude=None,
                      relroot=USE_CWD,
                      ):
    if relroot and relroot is not USE_CWD:
        relroot = os.path.abspath(relroot)
    if start:
        start = fix_filename(start, relroot, fixroot=False)
    if include:
        include = set(fix_filename(v, relroot, fixroot=False)
                      for v in include)
    if exclude:
        exclude = set(fix_filename(v, relroot, fixroot=False)
                      for v in exclude)

    onempty = Exception('no filenames provided')
    for filename, solo in iter_many(filenames, onempty):
        filename = fix_filename(filename, relroot, fixroot=False)
        relfile = format_filename(filename, relroot, fixroot=False, normalize=False)
        check, start = _get_check(filename, start, include, exclude)
        yield filename, relfile, check, solo