def _get_script_group_lines(grouped, script):
    if six.PY2:
        script = script.encode('utf-8')

    parts = shlex.split(script)

    for script_line, lines in reversed(grouped):
        if all(part in script_line for part in parts):
            return lines

    raise ScriptNotInLog