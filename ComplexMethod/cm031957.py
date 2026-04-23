def iter_marks(mark='.', *, group=5, groups=2, lines=_NOT_SET, sep=' '):
    mark = mark or ''
    group = group if group and group > 1 else 1
    groups = groups if groups and groups > 1 else 1

    sep = f'{mark}{sep}' if sep else mark
    end = f'{mark}{os.linesep}'
    div = os.linesep
    perline = group * groups
    if lines is _NOT_SET:
        # By default we try to put about 100 in each line group.
        perlines = 100 // perline * perline
    elif not lines or lines < 0:
        perlines = None
    else:
        perlines = perline * lines

    if perline == 1:
        yield end
    elif group == 1:
        yield sep

    count = 1
    while True:
        if count % perline == 0:
            yield end
            if perlines and count % perlines == 0:
                yield div
        elif count % group == 0:
            yield sep
        else:
            yield mark
        count += 1