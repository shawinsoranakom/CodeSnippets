def _format_side_effect_message(self, var: VariableTracker) -> str:
        """Format a side effect log message with user stack."""
        assert config.side_effect_replay_policy != "silent"
        locations = self.mutation_user_stacks.get(var, [])
        description = f"Mutating object of type {var.python_type_name()}"
        source_info = " (no source)"
        if var.source is not None:
            if isinstance(var.source, TempLocalSource):
                source_info = " (source: created in torch.compile region)"
            elif isinstance(var, variables.CellVariable) and var.local_name is not None:
                source_info = f" (source: {var.local_name})"
            elif isinstance(
                var, variables.torch_function.TorchFunctionModeStackVariable
            ):
                source_info = " (source: torch function mode stack mutation)"
            else:
                # NOTE: NotImplementedError from var.source.name is a bug and must be fixed!
                source_info = f" (source name: {var.source.name})"

        if locations:
            # Format and dedupe stacks using tuple representation for efficiency
            seen = set()
            unique_formatted_stacks: list[str] = []
            stack_above_dynamo = collapse_resume_frames(get_stack_above_dynamo())
            for stack in locations:
                # Use tuple of frame info for fast deduplication
                # Include position info (colno, end_lineno, end_colno) to distinguish
                # multiple mutations on the same line (when available in Python 3.11+)
                stack_tuple = tuple(
                    (
                        f.filename,
                        f.lineno,
                        f.name,
                        f.line,
                        getattr(f, "colno", None),
                        getattr(f, "end_lineno", None),
                        getattr(f, "end_colno", None),
                    )
                    for f in stack
                )
                if stack_tuple not in seen:
                    seen.add(stack_tuple)
                    stack_augmented = collapse_resume_frames(stack_above_dynamo + stack)
                    unique_formatted_stacks.append(
                        "".join(traceback.format_list(stack_augmented))
                    )
            formatted_lines: str = "\n********\n\n".join(unique_formatted_stacks)
            log_str = f"{description}{source_info}\n\n{textwrap.indent(formatted_lines, '    ')}"
        else:
            log_str = (
                f"{description}{source_info} (unable to find user stacks for mutations)"
            )

        return log_str