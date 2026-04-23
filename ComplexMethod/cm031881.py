def parse_table_lines(lines):
    lines = iter_clean_lines(lines)

    group = None
    prev = ''
    for line, rawline in lines:
        if line.startswith('## '):
            assert not rawline.startswith(' '), (line, rawline)
            if group:
                assert prev, (line, rawline)
                kind, after, _ = group
                assert kind and kind != 'section-group', (group, line, rawline)
                assert after is not None, (group, line, rawline)
            else:
                assert not prev, (prev, line, rawline)
                kind, after = group = ('section-group', None)
            title = line[3:].lstrip()
            assert title, (line, rawline)
            if after is not None:
                try:
                    line, rawline = next(lines)
                except StopIteration:
                    line = None
                if line != after:
                    raise NotImplementedError((group, line, rawline))
            yield kind, title
            group = None
        elif group:
            raise NotImplementedError((group, line, rawline))
        elif line.startswith('##---'):
            assert line.rstrip('-') == '##', (line, rawline)
            group = ('section-minor', '', line)
        elif line.startswith('#####'):
            assert not line.strip('#'), (line, rawline)
            group = ('section-major', '', line)
        elif line:
            yield 'row', line
        prev = line