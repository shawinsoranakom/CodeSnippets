def _is_on_hf_mount(path: "str | os.PathLike") -> bool:
    """True if `path` lives on an hf-mount FUSE filesystem (device string 'hf-mount').

    hf-mount's mmap + readahead interaction deadlocks under parallel page-faults,
    so callers should load the file into memory instead. Linux-only; returns False
    on other platforms.
    """
    if not sys.platform.startswith("linux"):
        return False
    try:
        real = os.path.realpath(os.fspath(path))
        with open("/proc/mounts", encoding="utf-8") as fh:
            entries = sorted(
                ((p[0], p[1]) for p in (l.split() for l in fh) if len(p) >= 2),
                key=lambda e: len(e[1]),
                reverse=True,
            )
        for dev, mp in entries:
            if real == mp or real.startswith(mp.rstrip("/") + "/"):
                return dev == "hf-mount"
    except (OSError, ValueError):
        pass
    return False