def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[JustifyMethod] = None,
        overflow: Optional[OverflowMethod] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: bool = True,
        soft_wrap: Optional[bool] = None,
        new_line_start: bool = False,
    ) -> None:
        """Print to the console.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): Justify method: "default", "left", "right", "center", or "full". Defaults to ``None``.
            overflow (str, optional): Overflow method: "ignore", "crop", "fold", or "ellipsis". Defaults to None.
            no_wrap (Optional[bool], optional): Disable word wrapping. Defaults to None.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to ``None``.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to ``None``.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default. Defaults to ``None``.
            width (Optional[int], optional): Width of output, or ``None`` to auto-detect. Defaults to ``None``.
            crop (Optional[bool], optional): Crop output to width of terminal. Defaults to True.
            soft_wrap (bool, optional): Enable soft wrap mode which disables word wrapping and cropping of text or ``None`` for
                Console default. Defaults to ``None``.
            new_line_start (bool, False): Insert a new line at the start if the output contains more than one line. Defaults to ``False``.
        """
        if not objects:
            if end == "\n":
                objects = (NewLine(),)
            else:
                objects = ("",)

        if soft_wrap is None:
            soft_wrap = self.soft_wrap
        if soft_wrap:
            if no_wrap is None:
                no_wrap = True
            if overflow is None:
                overflow = "ignore"
            crop = False
        render_hooks = self._render_hooks[:]
        with self:
            renderables = self._collect_renderables(
                objects,
                sep,
                end,
                justify=justify,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
            )
            for hook in render_hooks:
                renderables = hook.process_renderables(renderables)
            render_options = self.options.update(
                justify=justify,
                overflow=overflow,
                width=min(width, self.width) if width is not None else NO_CHANGE,
                height=height,
                no_wrap=no_wrap,
                markup=markup,
                highlight=highlight,
            )

            new_segments: List[Segment] = []
            extend = new_segments.extend
            render = self.render
            if style is None:
                for renderable in renderables:
                    extend(render(renderable, render_options))
            else:
                render_style = self.get_style(style)
                new_line = Segment.line()
                for renderable in renderables:
                    for line, add_new_line in Segment.split_lines_terminator(
                        render(renderable, render_options)
                    ):
                        extend(Segment.apply_style(line, render_style))
                        if add_new_line:
                            new_segments.append(new_line)

            if new_line_start:
                if (
                    len("".join(segment.text for segment in new_segments).splitlines())
                    > 1
                ):
                    new_segments.insert(0, Segment.line())
            if crop:
                buffer_extend = self._buffer.extend
                for line in Segment.split_and_crop_lines(
                    new_segments, self.width, pad=False
                ):
                    buffer_extend(line)
            else:
                self._buffer.extend(new_segments)