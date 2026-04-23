def handle_deduplication(module, mounts):
    """Return the unique mount points from the complete list of mounts, and handle the optional aggregate results."""
    mount_points = {}
    mounts_by_source = {}
    for mount in mounts:
        mount_point = mount["mount"]
        source = mount["ansible_context"]["source"]
        if mount_point not in mount_points:
            mount_points[mount_point] = mount
        mounts_by_source.setdefault(source, []).append(mount_point)

    duplicates_by_src = {src: mnts for src, mnts in mounts_by_source.items() if len(set(mnts)) != len(mnts)}
    if duplicates_by_src and module.params["include_aggregate_mounts"] is None:
        duplicates_by_src = {src: mnts for src, mnts in mounts_by_source.items() if len(set(mnts)) != len(mnts)}
        duplicates_str = ", ".join([f"{src} ({duplicates})" for src, duplicates in duplicates_by_src.items()])
        module.warn(f"mount_facts: ignoring repeat mounts in the following sources: {duplicates_str}. "
                    "You can disable this warning by configuring the 'include_aggregate_mounts' option as True or False.")

    if module.params["include_aggregate_mounts"]:
        aggregate_mounts = mounts
    else:
        aggregate_mounts = []

    return mount_points, aggregate_mounts