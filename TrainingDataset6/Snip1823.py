def get_output(script):
    """Gets command output from shell logger."""
    with logs.debug_time(u'Read output from external shell logger'):
        commands = _get_last_n(const.SHELL_LOGGER_LIMIT)
        for command in commands:
            if command['command'] == script:
                lines = _get_output_lines(command['output'])
                output = '\n'.join(lines).strip()
                return output
            else:
                logs.warn("Output isn't available in shell logger")
                return None