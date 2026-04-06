def _get_used_port(command):
    for pattern in patterns:
        matched = re.search(pattern, command.output)
        if matched:
            return matched.group('port')