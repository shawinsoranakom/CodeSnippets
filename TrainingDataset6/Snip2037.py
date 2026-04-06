def _get_all_tasks(gradle):
    proc = Popen([gradle, 'tasks'], stdout=PIPE)
    should_yield = False
    for line in proc.stdout.readlines():
        line = line.decode().strip()
        if line.startswith('----'):
            should_yield = True
            continue

        if not line.strip():
            should_yield = False
            continue

        if should_yield and not line.startswith('All tasks runnable from root project'):
            yield line.split(' ')[0]