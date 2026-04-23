def get_verbose_code_part(code_part: str, guard: Guard | None) -> str:
    extra = ""
    if guard is not None:
        if guard.user_stack:
            for fs in reversed(guard.user_stack):
                if fs.filename not in uninteresting_files():
                    extra = f"  # {format_frame(fs, line=True)}"
                    if len(extra) > 1024:
                        # For fx graphs, the line can be very long in case of
                        # torch.stack ops, where many inputs are set to None
                        # after the operation.  This increases the size of the
                        # guards log file.  In such cases, do not print the line
                        # contents.
                        extra = f"  # {format_frame(fs)}"
                    break
        elif guard.stack:
            summary = guard.stack.summary()
            if len(summary) > 0:
                extra = f"  # {format_frame(summary[-1])}"
            else:
                extra = "  # <unknown>"
    return f"{code_part:<60}{extra}"