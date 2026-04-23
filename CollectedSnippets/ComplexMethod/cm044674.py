def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        style = console.get_style(self.style)
        if self.expand:
            width = options.max_width
        else:
            width = min(
                Measurement.get(console, options, self.renderable).maximum
                + self.left
                + self.right,
                options.max_width,
            )
        render_options = options.update_width(width - self.left - self.right)
        if render_options.height is not None:
            render_options = render_options.update_height(
                height=render_options.height - self.top - self.bottom
            )
        lines = console.render_lines(
            self.renderable, render_options, style=style, pad=True
        )
        _Segment = Segment

        left = _Segment(" " * self.left, style) if self.left else None
        right = (
            [_Segment(f'{" " * self.right}', style), _Segment.line()]
            if self.right
            else [_Segment.line()]
        )
        blank_line: Optional[List[Segment]] = None
        if self.top:
            blank_line = [_Segment(f'{" " * width}\n', style)]
            yield from blank_line * self.top
        if left:
            for line in lines:
                yield left
                yield from line
                yield from right
        else:
            for line in lines:
                yield from line
                yield from right
        if self.bottom:
            blank_line = blank_line or [_Segment(f'{" " * width}\n', style)]
            yield from blank_line * self.bottom