def debug_string(self, show_stack_trace: bool | None = None) -> str:
        """
        show_stack_trace: option to display one-line stack trace summaries above groups
                        of operations (similar to gm.print_readable() style).
                        Requires record_stack_trace=True.
                        if None, uses self.record_stack_trace, otherwise overrides it.
        """
        show_stack_trace = (
            self.record_stack_trace if show_stack_trace is None else show_stack_trace
        )

        with torch._C.DisableTorchFunction():
            if not show_stack_trace:
                result = "\n".join(
                    "  "
                    + "  " * op.call_depth
                    + op.render(self.record_tensor_attributes)
                    for op in self.operators
                )
                return result

            # Group operations by stack trace
            lines = []
            prev_stack_summary = None

            for op in self.operators:
                # Get the stack trace: prefer fwd_stack_trace, fallback to stack_trace
                stack_trace = None
                if hasattr(op, "fwd_stack_trace") and op.fwd_stack_trace:
                    stack_trace = op.fwd_stack_trace
                elif hasattr(op, "stack_trace") and op.stack_trace:
                    stack_trace = op.stack_trace

                stack_summary = None
                if stack_trace:
                    stack_summary = _get_user_stack_trace(stack_trace)

                if stack_summary and stack_summary != prev_stack_summary:
                    # add blank line before stack trace comment for readability
                    if lines:  # don't add blank line at the very start
                        lines.append("")
                    indent = "  " * (op.call_depth + 1)
                    lines.append(indent + "# " + stack_summary)
                    prev_stack_summary = stack_summary

                # Add the operation line
                line = (
                    "  "
                    + "  " * op.call_depth
                    + op.render(self.record_tensor_attributes)
                )
                lines.append(line)

            return "\n".join(lines)