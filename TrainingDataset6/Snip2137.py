def _get_pid_by_port(port):
    proc = Popen(['lsof', '-i', ':{}'.format(port)], stdout=PIPE)
    lines = proc.stdout.read().decode().split('\n')
    if len(lines) > 1:
        return lines[1].split()[1]
    else:
        return None