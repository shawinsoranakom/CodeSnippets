def gen_aix_filesystems_entries(lines: list[str]) -> t.Iterable[MountInfoOptions]:
    """Yield tuples from /etc/filesystems https://www.ibm.com/docs/hu/aix/7.2?topic=files-filesystems-file.

    Each tuple contains the mount point, lines of origin, and the dictionary of the parsed lines.
    """
    for stanza in list_aix_filesystems_stanzas(lines):
        original = "\n".join(stanza)
        mount = stanza.pop(0)[:-1]  # snip trailing :
        mount_info: dict[str, str] = {}
        for line in stanza:
            attr, value = line.split("=", 1)
            mount_info[attr.strip()] = value.strip()

        device = ""
        if (nodename := mount_info.get("nodename")):
            device = nodename
        if (dev := mount_info.get("dev")):
            if device:
                device += ":"
            device += dev

        normalized_fields: dict[str, str | dict[str, str]] = {
            "mount": mount,
            "device": device or "unknown",
            "fstype": mount_info.get("vfs") or "unknown",
            # avoid clobbering the mount point with the AIX mount option "mount"
            "attributes": mount_info,
        }
        yield MountInfoOptions(mount, original, normalized_fields)