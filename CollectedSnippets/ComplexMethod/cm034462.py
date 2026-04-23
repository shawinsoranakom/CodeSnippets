def gen_mounts_by_source(module: AnsibleModule):
    """Iterate over the sources and yield tuples containing the source, mount point, source line(s), and the parsed result."""
    sources = get_sources(module)

    if len(set(sources)) < len(sources):
        module.warn(f"mount_facts option 'sources' contains duplicate entries, repeat sources will be ignored: {sources}")

    mount_fallback = module.params["mount_binary"] and set(sources).intersection(DYNAMIC_SOURCES)

    seen = set()
    for source in sources:
        if source in seen or (real_source := os.path.realpath(source)) in seen:
            continue

        if source == "mount":
            seen.add(source)
            stdout = run_mount_bin(module, module.params["mount_binary"])
            results = [(source, *astuple(mount_info)) for mount_info in gen_mounts_from_stdout(stdout)]
        else:
            seen.add(real_source)
            results = [(source, *astuple(mount_info)) for mount_info in gen_mounts_by_file(source)]

        if results and source in ("mount", *DYNAMIC_SOURCES):
            mount_fallback = False

        yield from results

    if mount_fallback:
        stdout = run_mount_bin(module, module.params["mount_binary"])
        yield from [("mount", *astuple(mount_info)) for mount_info in gen_mounts_from_stdout(stdout)]