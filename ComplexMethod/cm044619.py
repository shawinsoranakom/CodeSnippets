def _measure_column(
        self,
        console: "Console",
        options: "ConsoleOptions",
        column: Column,
    ) -> Measurement:
        """Get the minimum and maximum width of the column."""

        max_width = options.max_width
        if max_width < 1:
            return Measurement(0, 0)

        padding_width = self._get_padding_width(column._index)
        if column.width is not None:
            # Fixed width column
            return Measurement(
                column.width + padding_width, column.width + padding_width
            ).with_maximum(max_width)
        # Flexible column, we need to measure contents
        min_widths: List[int] = []
        max_widths: List[int] = []
        append_min = min_widths.append
        append_max = max_widths.append
        get_render_width = Measurement.get
        for cell in self._get_cells(console, column._index, column):
            _min, _max = get_render_width(console, options, cell.renderable)
            append_min(_min)
            append_max(_max)

        measurement = Measurement(
            max(min_widths) if min_widths else 1,
            max(max_widths) if max_widths else max_width,
        ).with_maximum(max_width)
        measurement = measurement.clamp(
            None if column.min_width is None else column.min_width + padding_width,
            None if column.max_width is None else column.max_width + padding_width,
        )
        return measurement