def run_cmd(cmd, live=False, readsize=10):
    cmdargs = shlex.split(cmd)

    # subprocess should be passed byte strings.
    cmdargs = [to_bytes(a, errors='surrogate_or_strict') for a in cmdargs]

    p = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout = b''
    stderr = b''
    rpipes = [p.stdout, p.stderr]
    while True:
        rfd, wfd, efd = select.select(rpipes, [], rpipes, 1)

        if p.stdout in rfd:
            dat = os.read(p.stdout.fileno(), readsize)
            if live:
                sys.stdout.buffer.write(dat)
            stdout += dat
            if dat == b'':
                rpipes.remove(p.stdout)
        if p.stderr in rfd:
            dat = os.read(p.stderr.fileno(), readsize)
            stderr += dat
            if live:
                sys.stdout.buffer.write(dat)
            if dat == b'':
                rpipes.remove(p.stderr)
        # only break out if we've emptied the pipes, or there is nothing to
        # read from and the process has finished.
        if (not rpipes or not rfd) and p.poll() is not None:
            break
        # Calling wait while there are still pipes to read can cause a lock
        elif not rpipes and p.poll() is None:
            p.wait()

    return p.returncode, stdout, stderr