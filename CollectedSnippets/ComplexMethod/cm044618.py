def _get_cells(
        self, console: "Console", column_index: int, column: Column
    ) -> Iterable[_Cell]:
        """Get all the cells with padding and optional header."""

        collapse_padding = self.collapse_padding
        pad_edge = self.pad_edge
        padding = self.padding
        any_padding = any(padding)

        first_column = column_index == 0
        last_column = column_index == len(self.columns) - 1

        _padding_cache: Dict[Tuple[bool, bool], Tuple[int, int, int, int]] = {}

        def get_padding(first_row: bool, last_row: bool) -> Tuple[int, int, int, int]:
            cached = _padding_cache.get((first_row, last_row))
            if cached:
                return cached
            top, right, bottom, left = padding

            if collapse_padding:
                if not first_column:
                    left = max(0, left - right)
                if not last_row:
                    bottom = max(0, top - bottom)

            if not pad_edge:
                if first_column:
                    left = 0
                if last_column:
                    right = 0
                if first_row:
                    top = 0
                if last_row:
                    bottom = 0
            _padding = (top, right, bottom, left)
            _padding_cache[(first_row, last_row)] = _padding
            return _padding

        raw_cells: List[Tuple[StyleType, "RenderableType"]] = []
        _append = raw_cells.append
        get_style = console.get_style
        if self.show_header:
            header_style = get_style(self.header_style or "") + get_style(
                column.header_style
            )
            _append((header_style, column.header))
        cell_style = get_style(column.style or "")
        for cell in column.cells:
            _append((cell_style, cell))
        if self.show_footer:
            footer_style = get_style(self.footer_style or "") + get_style(
                column.footer_style
            )
            _append((footer_style, column.footer))

        if any_padding:
            _Padding = Padding
            for first, last, (style, renderable) in loop_first_last(raw_cells):
                yield _Cell(
                    style,
                    _Padding(renderable, get_padding(first, last)),
                    getattr(renderable, "vertical", None) or column.vertical,
                )
        else:
            for style, renderable in raw_cells:
                yield _Cell(
                    style,
                    renderable,
                    getattr(renderable, "vertical", None) or column.vertical,
                )