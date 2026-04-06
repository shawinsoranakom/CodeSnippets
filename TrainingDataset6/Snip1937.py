def _get_all_commands():
    proc = subprocess.Popen(['gem', 'help', 'commands'],
                            stdout=subprocess.PIPE)

    for line in proc.stdout.readlines():
        line = line.decode()

        if line.startswith('    '):
            yield line.strip().split(' ')[0]