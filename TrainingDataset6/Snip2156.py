def _get_commands():
    proc = Popen(['react-native', '--help'], stdout=PIPE)
    should_yield = False
    for line in proc.stdout.readlines():
        line = line.decode().strip()

        if not line:
            continue

        if 'Commands:' in line:
            should_yield = True
            continue

        if should_yield:
            yield line.split(' ')[0]