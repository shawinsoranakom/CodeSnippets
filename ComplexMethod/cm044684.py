def _render_stack(self, stack: Stack) -> RenderResult:
        path_highlighter = PathHighlighter()
        theme = self.theme

        def render_locals(frame: Frame) -> Iterable[ConsoleRenderable]:
            if frame.locals:
                yield render_scope(
                    frame.locals,
                    title="locals",
                    indent_guides=self.indent_guides,
                    max_length=self.locals_max_length,
                    max_string=self.locals_max_string,
                    max_depth=self.locals_max_depth,
                    overflow=self.locals_overflow,
                )

        exclude_frames: Optional[range] = None
        if self.max_frames != 0:
            exclude_frames = range(
                self.max_frames // 2,
                len(stack.frames) - self.max_frames // 2,
            )

        excluded = False
        for frame_index, frame in enumerate(stack.frames):
            if exclude_frames and frame_index in exclude_frames:
                excluded = True
                continue

            if excluded:
                assert exclude_frames is not None
                yield Text(
                    f"\n... {len(exclude_frames)} frames hidden ...",
                    justify="center",
                    style="traceback.error",
                )
                excluded = False

            first = frame_index == 0
            frame_filename = frame.filename
            suppressed = any(frame_filename.startswith(path) for path in self.suppress)

            if os.path.exists(frame.filename):
                text = Text.assemble(
                    path_highlighter(Text(frame.filename, style="pygments.string")),
                    (":", "pygments.text"),
                    (str(frame.lineno), "pygments.number"),
                    " in ",
                    (frame.name, "pygments.function"),
                    style="pygments.text",
                )
            else:
                text = Text.assemble(
                    "in ",
                    (frame.name, "pygments.function"),
                    (":", "pygments.text"),
                    (str(frame.lineno), "pygments.number"),
                    style="pygments.text",
                )
            if not frame.filename.startswith("<") and not first:
                yield ""
            yield text
            if frame.filename.startswith("<"):
                yield from render_locals(frame)
                continue
            if not suppressed:
                try:
                    code_lines = linecache.getlines(frame.filename)
                    code = "".join(code_lines)
                    if not code:
                        # code may be an empty string if the file doesn't exist, OR
                        # if the traceback filename is generated dynamically
                        continue
                    lexer_name = self._guess_lexer(frame.filename, code)
                    syntax = Syntax(
                        code,
                        lexer_name,
                        theme=theme,
                        line_numbers=True,
                        line_range=(
                            frame.lineno - self.extra_lines,
                            frame.lineno + self.extra_lines,
                        ),
                        highlight_lines={frame.lineno},
                        word_wrap=self.word_wrap,
                        code_width=self.code_width,
                        indent_guides=self.indent_guides,
                        dedent=False,
                    )
                    yield ""
                except Exception as error:
                    yield Text.assemble(
                        (f"\n{error}", "traceback.error"),
                    )
                else:
                    if frame.last_instruction is not None:
                        start, end = frame.last_instruction

                        # Stylize a line at a time
                        # So that indentation isn't underlined (which looks bad)
                        for line1, column1, column2 in _iter_syntax_lines(start, end):
                            try:
                                if column1 == 0:
                                    line = code_lines[line1 - 1]
                                    column1 = len(line) - len(line.lstrip())
                                if column2 == -1:
                                    column2 = len(code_lines[line1 - 1])
                            except IndexError:
                                # Being defensive here
                                # If last_instruction reports a line out-of-bounds, we don't want to crash
                                continue

                            syntax.stylize_range(
                                style="traceback.error_range",
                                start=(line1, column1),
                                end=(line1, column2),
                            )
                    yield (
                        Columns(
                            [
                                syntax,
                                *render_locals(frame),
                            ],
                            padding=1,
                        )
                        if frame.locals
                        else syntax
                    )