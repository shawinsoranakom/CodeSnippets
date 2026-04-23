def get_mount_facts(module: AnsibleModule):
    """List and filter mounts, returning all mounts for each unique source."""
    seconds = module.params["timeout"]
    mounts = []
    for source, mount, origin, fields in gen_mounts_by_source(module):
        device = fields["device"]
        fstype = fields["fstype"]

        # Convert UUIDs in Linux /etc/fstab to device paths
        # TODO need similar for OpenBSD which lists UUIDS (without the UUID= prefix) in /etc/fstab, needs another approach though.
        uuid = None
        if device.startswith("UUID="):
            uuid = device.split("=", 1)[1]
            device = get_device_by_uuid(module, uuid) or device

        if not any(fnmatch(device, pattern) for pattern in module.params["devices"] or ["*"]):
            continue
        if not any(fnmatch(fstype, pattern) for pattern in module.params["fstypes"] or ["*"]):
            continue

        timed_func = _timeout.timeout(seconds, f"Timed out getting mount size for mount {mount} (type {fstype})")(get_mount_size)
        if mount_size := handle_timeout(module)(timed_func)(mount):
            fields.update(mount_size)

        if uuid is None:
            with suppress(subprocess.CalledProcessError):
                uuid = get_partition_uuid(module, device)

        fields.update({"ansible_context": {"source": source, "source_data": origin}, "uuid": uuid})
        mounts.append(fields)

    return mounts