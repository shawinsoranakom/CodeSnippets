def _get_failed_lifecycle(command):
    return re.search(r'\[ERROR\] Unknown lifecycle phase "(.+)"',
                     command.output)