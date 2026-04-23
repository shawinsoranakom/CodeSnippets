def parse_table(entries, sep, header=None, rawsep=None, *,
                default=NOT_SET,
                strict=True,
                ):
    header, sep = _normalize_table_file_props(header, sep)
    if not sep:
        raise ValueError('missing "sep"')

    ncols = None
    if header:
        if strict:
            ncols = len(header.split(sep))
        cur_file = None
    for line, filename in strutil.parse_entries(entries, ignoresep=sep):
        _sep = sep
        if filename:
            if header and cur_file != filename:
                cur_file = filename
                # Skip the first line if it's the header.
                if line.strip() == header:
                    continue
                else:
                    # We expected the header.
                    raise NotImplementedError((header, line))
        elif rawsep and sep not in line:
            _sep = rawsep

        row = _parse_row(line, _sep, ncols, default)
        if strict and not ncols:
            ncols = len(row)
        yield row, filename