def _get_possible_interfaces():
    proc = subprocess.Popen(['ifconfig', '-a'], stdout=subprocess.PIPE)
    for line in proc.stdout.readlines():
        line = line.decode()
        if line and line != '\n' and not line.startswith(' '):
            yield line.split(' ')[0]