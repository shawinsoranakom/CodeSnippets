def cmd_data(datacmd, filenames, known=None, *,
             _analyze=_analyze,
             formats=FORMATS,
             extracolumns=None,
             relroot=fsutil.USE_CWD,
             track_progress=None,
             **kwargs
             ):
    kwargs.pop('verbosity', None)
    usestdout = kwargs.pop('show', None)
    if datacmd == 'show':
        do_fmt = formats['summary']
        if isinstance(known, str):
            known, _ = _datafiles.get_known(known, extracolumns, relroot)
        for line in do_fmt(known):
            print(line)
    elif datacmd == 'dump':
        filenames, relroot = fsutil.fix_filenames(filenames, relroot=relroot)
        if track_progress:
            filenames = track_progress(filenames)
        analyzed = _analyze(filenames, **kwargs)
        analyzed.fix_filenames(relroot, normalize=False)
        if known is None or usestdout:
            outfile = io.StringIO()
            _datafiles.write_known(analyzed, outfile, extracolumns,
                                   relroot=relroot)
            print(outfile.getvalue())
        else:
            _datafiles.write_known(analyzed, known, extracolumns,
                                   relroot=relroot)
    elif datacmd == 'check':
        raise NotImplementedError(datacmd)
    else:
        raise ValueError(f'unsupported data command {datacmd!r}')