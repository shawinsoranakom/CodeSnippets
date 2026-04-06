def get_golang_commands():
    proc = subprocess.Popen('go', stderr=subprocess.PIPE)
    lines = [line.decode('utf-8').strip() for line in proc.stderr.readlines()]
    lines = dropwhile(lambda line: line != 'The commands are:', lines)
    lines = islice(lines, 2, None)
    lines = takewhile(lambda line: line, lines)
    return [line.split(' ')[0] for line in lines]