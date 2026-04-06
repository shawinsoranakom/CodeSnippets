def _get_operations():
    proc = subprocess.Popen(["dnf", '--help'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    lines = proc.stdout.read().decode("utf-8")

    return _parse_operations(lines)