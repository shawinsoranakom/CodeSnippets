def _get_all_tasks():
    proc = Popen(['grunt', '--help'], stdout=PIPE)
    should_yield = False
    for line in proc.stdout.readlines():
        line = line.decode().strip()

        if 'Available tasks' in line:
            should_yield = True
            continue

        if should_yield and not line:
            return

        if '  ' in line:
            yield line.split(' ')[0]