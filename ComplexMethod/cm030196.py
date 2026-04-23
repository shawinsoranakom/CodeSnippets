def unified_diff(a, b, fromfile='', tofile='', fromfiledate='',
                 tofiledate='', n=3, lineterm='\n', *, color=False):
    r"""
    Compare two sequences of lines; generate the delta as a unified diff.

    Unified diffs are a compact way of showing line changes and a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those with ---, +++, or @@) are
    created with a trailing newline.  This is helpful so that inputs
    created from file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs and outputs have trailing
    newlines.

    For inputs that do not have trailing newlines, set the lineterm
    argument to "" so that the output will be uniformly newline free.

    Set 'color' to True to enable output in color, similar to
    'git diff --color'. Even if enabled, it can be
    controlled using environment variables such as 'NO_COLOR'.

    The unidiff format normally has a header for filenames and modification
    times.  Any or all of these may be specified using strings for
    'fromfile', 'tofile', 'fromfiledate', and 'tofiledate'.
    The modification times are normally expressed in the ISO 8601 format.

    Example:

    >>> for line in unified_diff('one two three four'.split(),
    ...             'zero one tree four'.split(), 'Original', 'Current',
    ...             '2005-01-26 23:30:50', '2010-04-02 10:20:52',
    ...             lineterm=''):
    ...     print(line)                 # doctest: +NORMALIZE_WHITESPACE
    --- Original        2005-01-26 23:30:50
    +++ Current         2010-04-02 10:20:52
    @@ -1,4 +1,4 @@
    +zero
     one
    -two
    -three
    +tree
     four
    """

    if color and can_colorize():
        t = get_theme(force_color=True).difflib
    else:
        t = get_theme(force_no_color=True).difflib

    _check_types(a, b, fromfile, tofile, fromfiledate, tofiledate, lineterm)
    started = False
    for group in SequenceMatcher(None,a,b).get_grouped_opcodes(n):
        if not started:
            started = True
            fromdate = '\t{}'.format(fromfiledate) if fromfiledate else ''
            todate = '\t{}'.format(tofiledate) if tofiledate else ''
            yield f'{t.header}--- {fromfile}{fromdate}{lineterm}{t.reset}'
            yield f'{t.header}+++ {tofile}{todate}{lineterm}{t.reset}'

        first, last = group[0], group[-1]
        file1_range = _format_range_unified(first[1], last[2])
        file2_range = _format_range_unified(first[3], last[4])
        yield f'{t.hunk}@@ -{file1_range} +{file2_range} @@{lineterm}{t.reset}'

        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                for line in a[i1:i2]:
                    yield f'{t.context} {line}{t.reset}'
                continue
            if tag in {'replace', 'delete'}:
                for line in a[i1:i2]:
                    yield f'{t.removed}-{line}{t.reset}'
            if tag in {'replace', 'insert'}:
                for line in b[j1:j2]:
                    yield f'{t.added}+{line}{t.reset}'