def in_docker():
    """
    Returns True if running in a docker container, else False
    Ref. https://docs.docker.com/config/containers/runmetrics/#control-groups
    """
    if OVERRIDE_IN_DOCKER is not None:
        return OVERRIDE_IN_DOCKER

    # check some marker files that we create in our Dockerfiles
    for path in [
        "/usr/lib/localstack/.community-version",
        "/usr/lib/localstack/.pro-version",
        "/tmp/localstack/.marker",
    ]:
        if os.path.isfile(path):
            return True

    # details: https://github.com/localstack/localstack/pull/4352
    if os.path.exists("/.dockerenv"):
        return True
    if os.path.exists("/run/.containerenv"):
        return True

    if not os.path.exists("/proc/1/cgroup"):
        return False
    try:
        if any(
            [
                os.path.exists("/sys/fs/cgroup/memory/docker/"),
                any(
                    "docker-" in file_names
                    for file_names in os.listdir("/sys/fs/cgroup/memory/system.slice")
                ),
                os.path.exists("/sys/fs/cgroup/docker/"),
                any(
                    "docker-" in file_names
                    for file_names in os.listdir("/sys/fs/cgroup/system.slice/")
                ),
            ]
        ):
            return False
    except Exception:
        pass
    with open("/proc/1/cgroup") as ifh:
        content = ifh.read()
        if "docker" in content or "buildkit" in content:
            return True
        os_hostname = socket.gethostname()
        if os_hostname and os_hostname in content:
            return True

    # containerd does not set any specific file or config, but it does use
    # io.containerd.snapshotter.v1.overlayfs as the overlay filesystem for `/`.
    try:
        with open("/proc/mounts") as infile:
            for line in infile:
                line = line.strip()

                if not line:
                    continue

                # skip comments
                if line[0] == "#":
                    continue

                # format (man 5 fstab)
                # <spec> <mount point> <type> <options> <rest>...
                parts = line.split()
                if len(parts) < 4:
                    # badly formatted line
                    continue

                mount_point = parts[1]
                options = parts[3]

                # only consider the root filesystem
                if mount_point != "/":
                    continue

                if "io.containerd" in options:
                    return True

    except FileNotFoundError:
        pass

    return False