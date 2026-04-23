def render_table(header_row, data, delim=False, extra_gap=0, hide_empty=False):
    """ Render a list of rows, each as a list of values.
    Text after a \t will be right aligned """
    def width(string):
        return len(remove_terminal_sequences(string).replace('\t', ''))

    def get_max_lens(table):
        return [max(width(str(v)) for v in col) for col in zip(*table, strict=True)]

    def filter_using_list(row, filter_array):
        return [col for take, col in itertools.zip_longest(filter_array, row, fillvalue=True) if take]

    max_lens = get_max_lens(data) if hide_empty else []
    header_row = filter_using_list(header_row, max_lens)
    data = [filter_using_list(row, max_lens) for row in data]

    table = [header_row, *data]
    max_lens = get_max_lens(table)
    extra_gap += 1
    if delim:
        table = [header_row, [delim * (ml + extra_gap) for ml in max_lens], *data]
        table[1][-1] = table[1][-1][:-extra_gap * len(delim)]  # Remove extra_gap from end of delimiter
    for row in table:
        for pos, text in enumerate(map(str, row)):
            if '\t' in text:
                row[pos] = text.replace('\t', ' ' * (max_lens[pos] - width(text))) + ' ' * extra_gap
            else:
                row[pos] = text + ' ' * (max_lens[pos] - width(text) + extra_gap)
    return '\n'.join(''.join(row).rstrip() for row in table)