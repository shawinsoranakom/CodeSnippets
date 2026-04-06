def get_output(script, expanded):
    """Runs the script and obtains stdin/stderr.

    :type script: str
    :type expanded: str
    :rtype: str | None

    """
    env = dict(os.environ)
    env.update(settings.env)

    if six.PY2:
        expanded = expanded.encode('utf-8')

    split_expand = shlex.split(expanded)
    is_slow = split_expand[0] in settings.slow_commands if split_expand else False
    with logs.debug_time(u'Call: {}; with env: {}; is slow: {}'.format(
            script, env, is_slow)):
        result = Popen(expanded, shell=True, stdin=PIPE,
                       stdout=PIPE, stderr=STDOUT, env=env)
        if _wait_output(result, is_slow):
            output = result.stdout.read().decode('utf-8', errors='replace')
            logs.debug(u'Received output: {}'.format(output))
            return output
        else:
            logs.debug(u'Execution timed out!')
            return None