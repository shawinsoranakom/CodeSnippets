def render_stack(stack: Stack, last: bool) -> RenderResult:
            if stack.frames:
                stack_renderable: ConsoleRenderable = Panel(
                    self._render_stack(stack),
                    title="[traceback.title]Traceback [dim](most recent call last)",
                    style=background_style,
                    border_style="traceback.border",
                    expand=True,
                    padding=(0, 1),
                )
                stack_renderable = Constrain(stack_renderable, self.width)
                with console.use_theme(traceback_theme):
                    yield stack_renderable

            if stack.syntax_error is not None:
                with console.use_theme(traceback_theme):
                    yield Constrain(
                        Panel(
                            self._render_syntax_error(stack.syntax_error),
                            style=background_style,
                            border_style="traceback.border.syntax_error",
                            expand=True,
                            padding=(0, 1),
                            width=self.width,
                        ),
                        self.width,
                    )
                yield Text.assemble(
                    (f"{stack.exc_type}: ", "traceback.exc_type"),
                    highlighter(stack.syntax_error.msg),
                )
            elif stack.exc_value:
                yield Text.assemble(
                    (f"{stack.exc_type}: ", "traceback.exc_type"),
                    highlighter(stack.exc_value),
                )
            else:
                yield Text.assemble((f"{stack.exc_type}", "traceback.exc_type"))

            for note in stack.notes:
                yield Text.assemble(("[NOTE] ", "traceback.note"), highlighter(note))

            if stack.is_group:
                for group_no, group_exception in enumerate(stack.exceptions, 1):
                    grouped_exceptions: List[Group] = []
                    for group_last, group_stack in loop_last(group_exception.stacks):
                        grouped_exceptions.append(render_stack(group_stack, group_last))
                    yield ""
                    yield Constrain(
                        Panel(
                            Group(*grouped_exceptions),
                            title=f"Sub-exception #{group_no}",
                            border_style="traceback.group.border",
                        ),
                        self.width,
                    )

            if not last:
                if stack.is_cause:
                    yield Text.from_markup(
                        "\n[i]The above exception was the direct cause of the following exception:\n",
                    )
                else:
                    yield Text.from_markup(
                        "\n[i]During handling of the above exception, another exception occurred:\n",
                    )