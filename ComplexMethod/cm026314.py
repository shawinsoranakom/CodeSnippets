def _figure_out_source(
    record: logging.LogRecord,
    paths_re: re.Pattern[str],
    extracted_tb: list[tuple[FrameType, int]] | None = None,
) -> tuple[str, int]:
    """Figure out where a log message came from."""
    # If a stack trace exists, extract file names from the entire call stack.
    # The other case is when a regular "log" is made (without an attached
    # exception). In that case, just use the file where the log was made from.
    if record.exc_info:
        source: list[tuple[FrameType, int]] = extracted_tb or list(
            traceback.walk_tb(record.exc_info[2])
        )
        stack = [
            (tb_frame.f_code.co_filename, tb_line_no) for tb_frame, tb_line_no in source
        ]
        for i, (filename, _) in enumerate(stack):
            # Slice the stack to the first frame that matches
            # the record pathname.
            if filename == record.pathname:
                stack = stack[0 : i + 1]
                break
        # Iterate through the stack call (in reverse) and find the last call from
        # a file in Home Assistant. Try to figure out where error happened.
        for path, line_number in reversed(stack):
            # Try to match with a file within Home Assistant
            if match := paths_re.match(path):
                return (cast(str, match.group(1)), line_number)
    else:
        #
        # We need to figure out where the log call came from if we
        # don't have an exception.
        #
        # We do this by walking up the stack until we find the first
        # frame match the record pathname so the code below
        # can be used to reverse the remaining stack frames
        # and find the first one that is from a file within Home Assistant.
        #
        # We do not call traceback.extract_stack() because it is
        # it makes many stat() syscalls calls which do blocking I/O,
        # and since this code is running in the event loop, we need to avoid
        # blocking I/O.

        frame = sys._getframe(4)  # noqa: SLF001
        #
        # We use _getframe with 4 to skip the following frames:
        #
        # Jump 2 frames up to get to the actual caller
        # since we are in a function, and always called from another function
        # that are never the original source of the log message.
        #
        # Next try to skip any frames that are from the logging module
        # We know that the logger module typically has 5 frames itself
        # but it may change in the future so we are conservative and
        # only skip 2.
        #
        # _getframe is cpython only but we are already using cpython specific
        # code everywhere in HA so it's fine as its unlikely we will ever
        # support other python implementations.
        #
        # Iterate through the stack call (in reverse) and find the last call from
        # a file in Home Assistant. Try to figure out where error happened.
        while back := frame.f_back:
            if match := paths_re.match(frame.f_code.co_filename):
                return (cast(str, match.group(1)), frame.f_lineno)
            frame = back

    # Ok, we don't know what this is
    return (record.pathname, record.lineno)