def gen_mounts_from_stdout(stdout: str) -> t.Iterable[MountInfo]:
    """List mount dictionaries from mount stdout."""
    if not (pattern := get_mount_pattern(stdout)):
        stdout = ""

    for line in stdout.splitlines():
        if not (match := pattern.match(line)):
            # AIX has a couple header lines for some reason
            # MacOS "map" lines are skipped (e.g. "map auto_home on /System/Volumes/Data/home (autofs, automounted, nobrowse)")
            # TODO: include MacOS lines
            continue

        mount = match.groupdict()["mount"]
        if pattern is LINUX_MOUNT_RE:
            mount_info = match.groupdict()
        elif pattern is BSD_MOUNT_RE:
            # the group containing fstype is comma separated, and may include whitespace
            mount_info = match.groupdict()
            parts = re.split(r"\s*,\s*", match.group("fstype"), maxsplit=1)
            if len(parts) == 1:
                mount_info["fstype"] = parts[0]
            else:
                mount_info.update({"fstype": parts[0], "options": parts[1]})
        elif pattern is AIX_MOUNT_RE:
            mount_info = match.groupdict()
            device = mount_info.pop("mounted")
            node = mount_info.pop("node")
            if device and node:
                device = f"{node}:{device}"
            mount_info["device"] = device

        yield MountInfo(mount, line, mount_info)