def _is_tar_extract(cmd):
    if '--extract' in cmd:
        return True

    cmd = cmd.split()

    return len(cmd) > 1 and 'x' in cmd[1]