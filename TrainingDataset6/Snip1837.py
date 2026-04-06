def _get_operations(app):
    proc = subprocess.Popen([app, '--help'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    lines = proc.stdout.readlines()

    if app == 'apt':
        return _parse_apt_operations(lines)
    else:
        return _parse_apt_get_and_cache_operations(lines)