def parse_location_table(firstlineno, linetable):
    line = firstlineno
    addr = 0
    it = iter(linetable)
    while True:
        try:
            first_byte = read(it)
        except StopIteration:
            return
        code = (first_byte >> 3) & 15
        length = (first_byte & 7) + 1
        end_addr = addr + length
        if code == 15:
            yield addr, end_addr, None
            addr = end_addr
            continue
        elif code == 14: # Long form
            line_delta = read_signed_varint(it)
            line += line_delta
            end_line = line + read_varint(it)
            col = read_varint(it)
            end_col = read_varint(it)
        elif code == 13: # No column
            line_delta = read_signed_varint(it)
            line += line_delta
        elif code in (10, 11, 12): # new line
            line_delta = code - 10
            line += line_delta
            column = read(it)
            end_column = read(it)
        else:
            assert (0 <= code < 10)
            second_byte = read(it)
            column = code << 3 | (second_byte >> 4)
        yield addr, end_addr, line
        addr = end_addr