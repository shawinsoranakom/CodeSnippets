def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        align = self.align
        width = console.measure(self.renderable, options=options).maximum
        rendered = console.render(
            Constrain(
                self.renderable, width if self.width is None else min(width, self.width)
            ),
            options.update(height=None),
        )
        lines = list(Segment.split_lines(rendered))
        width, height = Segment.get_shape(lines)
        lines = Segment.set_shape(lines, width, height)
        new_line = Segment.line()
        excess_space = options.max_width - width
        style = console.get_style(self.style) if self.style is not None else None

        def generate_segments() -> Iterable[Segment]:
            if excess_space <= 0:
                # Exact fit
                for line in lines:
                    yield from line
                    yield new_line

            elif align == "left":
                # Pad on the right
                pad = Segment(" " * excess_space, style) if self.pad else None
                for line in lines:
                    yield from line
                    if pad:
                        yield pad
                    yield new_line

            elif align == "center":
                # Pad left and right
                left = excess_space // 2
                pad = Segment(" " * left, style)
                pad_right = (
                    Segment(" " * (excess_space - left), style) if self.pad else None
                )
                for line in lines:
                    if left:
                        yield pad
                    yield from line
                    if pad_right:
                        yield pad_right
                    yield new_line

            elif align == "right":
                # Padding on left
                pad = Segment(" " * excess_space, style)
                for line in lines:
                    yield pad
                    yield from line
                    yield new_line

        blank_line = (
            Segment(f"{' ' * (self.width or options.max_width)}\n", style)
            if self.pad
            else Segment("\n")
        )

        def blank_lines(count: int) -> Iterable[Segment]:
            if count > 0:
                for _ in range(count):
                    yield blank_line

        vertical_height = self.height or options.height
        iter_segments: Iterable[Segment]
        if self.vertical and vertical_height is not None:
            if self.vertical == "top":
                bottom_space = vertical_height - height
                iter_segments = chain(generate_segments(), blank_lines(bottom_space))
            elif self.vertical == "middle":
                top_space = (vertical_height - height) // 2
                bottom_space = vertical_height - top_space - height
                iter_segments = chain(
                    blank_lines(top_space),
                    generate_segments(),
                    blank_lines(bottom_space),
                )
            else:  #  self.vertical == "bottom":
                top_space = vertical_height - height
                iter_segments = chain(blank_lines(top_space), generate_segments())
        else:
            iter_segments = generate_segments()
        if self.style:
            style = console.get_style(self.style)
            iter_segments = Segment.apply_style(iter_segments, style)
        yield from iter_segments