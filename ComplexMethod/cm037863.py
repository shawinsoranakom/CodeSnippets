def _get_fs_type(files: list[str]) -> str:
    """Get the filesystem type of the first file in *files* (Linux only)."""
    if not files:
        return ""
    try:
        # Only the first file is checked — all checkpoint shards reside
        # in the same directory and therefore on the same filesystem.
        resolved = os.path.realpath(files[0])
        best_mount = ""
        best_fstype = ""
        # /proc/mounts may contain nested mount points (e.g. "/" -> ext4,
        # "/data" -> nfs4, "/data/local" -> ext4).  We pick the entry with
        # the longest matching mount_point — the same "longest prefix match"
        # rule the kernel uses to decide which filesystem serves a path.
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue
                mount_point, fstype = parts[1], parts[2]
                if (
                    resolved == mount_point
                    or resolved.startswith(os.path.join(mount_point, ""))
                ) and len(mount_point) > len(best_mount):
                    best_mount = mount_point
                    best_fstype = fstype
        return best_fstype
    except Exception:
        # /proc/mounts is Linux-specific; on other OSes (or if the read
        # fails for any reason) we fall back to an empty string.
        return ""