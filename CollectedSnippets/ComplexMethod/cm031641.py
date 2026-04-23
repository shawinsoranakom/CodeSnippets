def proxyval(self, visited):
        compact = self.field('_base')
        ascii = compact['_base']
        state = ascii['state']
        is_compact_ascii = (int(state['ascii']) and int(state['compact']))
        field_length = int(ascii['length'])
        if is_compact_ascii:
            field_str = ascii.address + 1
        elif int(state['compact']):
            field_str = compact.address + 1
        else:
            field_str = self.field('data')['any']
        repr_kind = int(state['kind'])
        if repr_kind == 1:
            field_str = field_str.cast(_type_unsigned_char_ptr())
        elif repr_kind == 2:
            field_str = field_str.cast(_type_unsigned_short_ptr())
        elif repr_kind == 4:
            field_str = field_str.cast(_type_unsigned_int_ptr())

        # Gather a list of ints from the code point array; these are either
        # UCS-1, UCS-2 or UCS-4 code points:
        code_points = [int(field_str[i]) for i in safe_range(field_length)]

        # Convert the int code points to unicode characters, and generate a
        # local unicode instance.
        result = ''.join(map(chr, code_points))
        return result