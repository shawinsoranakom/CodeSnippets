def get_mount_pattern(stdout: str):
    lines = stdout.splitlines()
    pattern = None
    if all(LINUX_MOUNT_RE.match(line) for line in lines):
        pattern = LINUX_MOUNT_RE
    elif all(BSD_MOUNT_RE.match(line) for line in lines if not line.startswith("map ")):
        pattern = BSD_MOUNT_RE
    elif len(lines) > 2 and all(AIX_MOUNT_RE.match(line) for line in lines[2:]):
        pattern = AIX_MOUNT_RE
    return pattern