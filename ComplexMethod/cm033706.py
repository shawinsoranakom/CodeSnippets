def enumerate_powershell_lines(
    path: str,
    collection_search_re: t.Optional[t.Pattern],
    collection_sub_re: t.Optional[t.Pattern],
) -> c.Generator[tuple[str, dict[int, int]], None, None]:
    """Enumerate PowerShell code coverage lines in the given file."""
    if os.path.getsize(path) == 0:
        display.warning('Empty coverage file: %s' % path, verbosity=2)
        return

    try:
        coverage_run = read_json_file(path)
    except Exception as ex:  # pylint: disable=locally-disabled, broad-except
        display.error('%s' % ex)
        return

    for filename, hits in coverage_run.items():
        filename = sanitize_filename(filename, collection_search_re=collection_search_re, collection_sub_re=collection_sub_re)

        if not filename:
            continue

        if isinstance(hits, dict) and not hits.get('Line'):
            # Input data was previously aggregated and thus uses the standard ansible-test output format for PowerShell coverage.
            # This format differs from the more verbose format of raw coverage data from the remote Windows hosts.
            hits = dict((int(key), value) for key, value in hits.items())

            yield filename, hits
            continue

        # PowerShell unpacks arrays if there's only a single entry so this is a defensive check on that
        if not isinstance(hits, list):
            hits = [hits]

        hits = dict((hit['Line'], hit['HitCount']) for hit in hits if hit)

        yield filename, hits