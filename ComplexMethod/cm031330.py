def _parse_terminfo_file(self, terminal_name: str) -> None:
        """Parse a terminfo file.

        Populate the _capabilities dict for easy retrieval

        Based on ncurses implementation in:
        - ncurses/tinfo/read_entry.c:_nc_read_termtype()
        - ncurses/tinfo/read_entry.c:_nc_read_file_entry()
        - ncurses/tinfo/lib_ti.c:tigetstr()
        """
        data = _read_terminfo_file(terminal_name)
        too_short = f"TermInfo file for {terminal_name!r} too short"
        offset = 12
        if len(data) < offset:
            raise ValueError(too_short)

        magic, name_size, bool_count, num_count, str_count, str_size = (
            struct.unpack("<Hhhhhh", data[:offset])
        )

        if magic == MAGIC16:
            number_size = 2
        elif magic == MAGIC32:
            number_size = 4
        else:
            raise ValueError(
                f"TermInfo file for {terminal_name!r} uses unknown magic"
            )

        # Skip data than PyREPL doesn't need:
        # - names (`|`-separated ASCII strings)
        # - boolean capabilities (bytes with value 0 or 1)
        # - numbers (little-endian integers, `number_size` bytes each)
        offset += name_size
        offset += bool_count
        if offset % 2:
            # Align to even byte boundary for numbers
            offset += 1
        offset += num_count * number_size
        if offset > len(data):
            raise ValueError(too_short)

        # Read string offsets
        end_offset = offset + 2 * str_count
        if offset > len(data):
            raise ValueError(too_short)
        string_offset_data = data[offset:end_offset]
        string_offsets = [
            off for [off] in struct.iter_unpack("<h", string_offset_data)
        ]
        offset = end_offset

        # Read string table
        if offset + str_size > len(data):
            raise ValueError(too_short)
        string_table = data[offset : offset + str_size]

        # Extract strings from string table
        capabilities = {}
        for cap, off in zip(_STRING_NAMES, string_offsets):
            if off < 0:
                # CANCELLED_STRING; we do not store those
                continue
            elif off < len(string_table):
                # Find null terminator
                end = string_table.find(0, off)
                if end >= 0:
                    capabilities[cap] = string_table[off:end]
            # in other cases this is ABSENT_STRING; we don't store those.

        # Note: we don't support extended capabilities since PyREPL doesn't
        # need them.

        self._capabilities = capabilities