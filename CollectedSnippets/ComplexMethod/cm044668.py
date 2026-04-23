def log(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[Union[str, Style]] = None,
        justify: Optional[JustifyMethod] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        log_locals: bool = False,
        _stack_offset: int = 1,
    ) -> None:
        """Log rich content to the terminal.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): One of "left", "right", "center", or "full". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to None.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to None.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default. Defaults to None.
            log_locals (bool, optional): Boolean to enable logging of locals where ``log()``
                was called. Defaults to False.
            _stack_offset (int, optional): Offset of caller from end of call stack. Defaults to 1.
        """
        if not objects:
            objects = (NewLine(),)

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
            if style is not None:
                renderables = [Styled(renderable, style) for renderable in renderables]

            filename, line_no, locals = self._caller_frame_info(_stack_offset)
            link_path = None if filename.startswith("<") else os.path.abspath(filename)
            path = filename.rpartition(os.sep)[-1]
            if log_locals:
                from .scope import render_scope

                locals_map = {
                    key: value
                    for key, value in locals.items()
                    if not key.startswith("__")
                }
                renderables.append(render_scope(locals_map, title="[i]locals"))

            renderables = [
                self._log_render(
                    self,
                    renderables,
                    log_time=self.get_datetime(),
                    path=path,
                    line_no=line_no,
                    link_path=link_path,
                )
            ]
            for hook in render_hooks:
                renderables = hook.process_renderables(renderables)
            new_segments: List[Segment] = []
            extend = new_segments.extend
            render = self.render
            render_options = self.options
            for renderable in renderables:
                extend(render(renderable, render_options))
            buffer_extend = self._buffer.extend
            for line in Segment.split_and_crop_lines(
                new_segments, self.width, pad=False
            ):
                buffer_extend(line)