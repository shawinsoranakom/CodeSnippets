def _get_operations():
    proc = subprocess.Popen('yum', stdout=subprocess.PIPE)

    lines = proc.stdout.readlines()
    lines = [line.decode('utf-8') for line in lines]
    lines = dropwhile(lambda line: not line.startswith("List of Commands:"), lines)
    lines = islice(lines, 2, None)
    lines = list(takewhile(lambda line: line.strip(), lines))
    return [line.strip().split(' ')[0] for line in lines]