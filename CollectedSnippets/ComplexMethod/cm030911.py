def parse_location_table(code):
    line = code.co_firstlineno
    it = iter(code.co_linetable)
    while True:
        try:
            first_byte = read(it)
        except StopIteration:
            return
        code = (first_byte >> 3) & 15
        length = (first_byte & 7) + 1
        if code == 15:
            yield (code, length, None, None, None, None)
        elif code == 14:
            line_delta = read_signed_varint(it)
            line += line_delta
            end_line = line + read_varint(it)
            col = read_varint(it)
            if col == 0:
                col = None
            else:
                col -= 1
            end_col = read_varint(it)
            if end_col == 0:
                end_col = None
            else:
                end_col -= 1
            yield (code, length, line, end_line, col, end_col)
        elif code == 13: # No column
            line_delta = read_signed_varint(it)
            line += line_delta
            yield (code, length, line, line, None, None)
        elif code in (10, 11, 12): # new line
            line_delta = code - 10
            line += line_delta
            column = read(it)
            end_column = read(it)
            yield (code, length, line, line, column, end_column)
        else:
            assert (0 <= code < 10)
            second_byte = read(it)
            column = code << 3 | (second_byte >> 4)
            yield (code, length, line, line, column, column + (second_byte & 15))