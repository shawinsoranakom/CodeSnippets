def get_parsed_diff(name: str) -> list[FileDiff]:
    """Parse and return the named git diff."""
    cache = pathlib.Path(__file__).parent / 'diff' / f'{name}.diff'
    content = cache.read_text()
    lines = content.splitlines()

    assert lines

    # noinspection PyProtectedMember
    from ansible_test._internal.diff import parse_diff

    diffs = parse_diff(lines)

    assert diffs

    for item in diffs:
        assert item.headers
        assert item.is_complete

        item.old.format_lines()
        item.new.format_lines()

        for line_range in item.old.ranges:
            assert line_range[1] >= line_range[0] > 0

        for line_range in item.new.ranges:
            assert line_range[1] >= line_range[0] > 0

    return diffs