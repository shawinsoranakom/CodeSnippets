def cmd_capi(filenames=None, *,
             levels=None,
             kinds=None,
             groupby='kind',
             format='table',
             showempty=None,
             ignored=None,
             track_progress=None,
             verbosity=VERBOSITY,
             **kwargs
             ):
    render = _capi.get_renderer(format)

    filenames = _files.iter_header_files(filenames, levels=levels)
    #filenames = (file for file, _ in main_for_filenames(filenames))
    if track_progress:
        filenames = track_progress(filenames)
    items = _capi.iter_capi(filenames)
    if levels:
        items = (item for item in items if item.level in levels)
    if kinds:
        items = (item for item in items if item.kind in kinds)

    filter = _capi.resolve_filter(ignored)
    if filter:
        items = (item for item in items if filter(item, log=lambda msg: logger.log(1, msg)))

    lines = render(
        items,
        groupby=groupby,
        showempty=showempty,
        verbose=verbosity > VERBOSITY,
    )
    print()
    for line in lines:
        print(line)