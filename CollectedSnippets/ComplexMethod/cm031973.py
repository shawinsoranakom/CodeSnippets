def cmd_check(filenames, *,
              checks=None,
              ignored=None,
              fmt=None,
              failfast=False,
              iter_filenames=None,
              relroot=fsutil.USE_CWD,
              track_progress=None,
              verbosity=VERBOSITY,
              _analyze=_analyze,
              _CHECKS=CHECKS,
              **kwargs
              ):
    if not checks:
        checks = _CHECKS
    elif isinstance(checks, str):
        checks = [checks]
    checks = [_CHECKS[c] if isinstance(c, str) else c
              for c in checks]
    printer = Printer(verbosity)
    (handle_failure, handle_after, div
     ) = _get_check_handlers(fmt, printer, verbosity)

    filenames, relroot = fsutil.fix_filenames(filenames, relroot=relroot)
    filenames = filter_filenames(filenames, iter_filenames, relroot)
    if track_progress:
        filenames = track_progress(filenames)

    logger.info('analyzing files...')
    analyzed = _analyze(filenames, **kwargs)
    analyzed.fix_filenames(relroot, normalize=False)
    decls = filter_forward(analyzed, markpublic=True)

    logger.info('checking analysis results...')
    failed = []
    for data, failure in _check_all(decls, checks, failfast=failfast):
        if data is None:
            printer.info('stopping after one failure')
            break
        if div is not None and len(failed) > 0:
            printer.info(div)
        failed.append(data)
        handle_failure(failure, data)
    handle_after()

    printer.info('-------------------------')
    logger.info(f'total failures: {len(failed)}')
    logger.info('done checking')

    if fmt == 'summary':
        print('Categorized by storage:')
        print()
        from .match import group_by_storage
        grouped = group_by_storage(failed, ignore_non_match=False)
        for group, decls in grouped.items():
            print()
            print(group)
            for decl in decls:
                print(' ', _fmt_one_summary(decl))
            print(f'subtotal: {len(decls)}')

    if len(failed) > 0:
        sys.exit(len(failed))