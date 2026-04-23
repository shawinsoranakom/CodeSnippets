def gather_ids(htmldir, *, verbose_print):
    if not htmldir.joinpath('objects.inv').exists():
        raise ValueError(f'{htmldir!r} is not a Sphinx HTML output directory')

    if sys._is_gil_enabled:
        pool = concurrent.futures.ProcessPoolExecutor()
    else:
        pool = concurrent.futures.ThreadPoolExecutor()
    tasks = {}
    for path in htmldir.glob('**/*.html'):
        relative_path = path.relative_to(htmldir)
        if '_static' in relative_path.parts:
            continue
        if 'whatsnew' in relative_path.parts:
            continue
        tasks[relative_path] = pool.submit(get_ids_from_file, path=path)

    ids_by_page = {}
    for relative_path, future in tasks.items():
        verbose_print(relative_path)
        ids = future.result()
        ids_by_page[str(relative_path)] = ids
        verbose_print(f'    - {len(ids)} ids found')

    common = set.intersection(*ids_by_page.values())
    verbose_print(f'Filtering out {len(common)} common ids')
    for key, page_ids in ids_by_page.items():
        ids_by_page[key] = sorted(page_ids - common)

    return ids_by_page