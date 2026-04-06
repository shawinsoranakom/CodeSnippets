def get_gulp_tasks():
    proc = subprocess.Popen(['gulp', '--tasks-simple'],
                            stdout=subprocess.PIPE)
    return [line.decode('utf-8')[:-1]
            for line in proc.stdout.readlines()]