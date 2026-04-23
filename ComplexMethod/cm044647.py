def _split_cells(cls, segment: "Segment", cut: int) -> Tuple["Segment", "Segment"]:
        """Split a segment in to two at a given cell position.

        Note that splitting a double-width character, may result in that character turning
        into two spaces.

        Args:
            segment (Segment): A segment to split.
            cut (int): A cell position to cut on.

        Returns:
            A tuple of two segments.
        """
        text, style, control = segment
        _Segment = Segment
        cell_length = segment.cell_length
        if cut >= cell_length:
            return segment, _Segment("", style, control)

        cell_size = get_character_cell_size

        pos = int((cut / cell_length) * len(text))

        while True:
            before = text[:pos]
            cell_pos = cell_len(before)
            out_by = cell_pos - cut
            if not out_by:
                return (
                    _Segment(before, style, control),
                    _Segment(text[pos:], style, control),
                )
            if out_by == -1 and cell_size(text[pos]) == 2:
                return (
                    _Segment(text[:pos] + " ", style, control),
                    _Segment(" " + text[pos + 1 :], style, control),
                )
            if out_by == +1 and cell_size(text[pos - 1]) == 2:
                return (
                    _Segment(text[: pos - 1] + " ", style, control),
                    _Segment(" " + text[pos:], style, control),
                )
            if cell_pos < cut:
                pos += 1
            else:
                pos -= 1