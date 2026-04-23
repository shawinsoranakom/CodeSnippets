def clean(context: argparse.Namespace, target: str | None = None) -> None:
    """The implementation of the "clean" command."""
    if target is None:
        target = context.host

    # If we're explicitly targeting the build, there's no platform or
    # distribution artefacts. If we're cleaning tests, we keep all built
    # artefacts. Otherwise, the built artefacts must be dirty, so we remove
    # them.
    if target not in {"build", "test"}:
        paths = ["dist", context.platform] + list(HOSTS[context.platform])
    else:
        paths = []

    if target in {"all", "build"}:
        paths.append("build")

    if target in {"all", "hosts"}:
        paths.extend(all_host_triples(context.platform))
    elif target not in {"build", "test", "package"}:
        paths.append(target)

    if target in {"all", "hosts", "test"}:
        paths.extend([
            path.name
            for path in CROSS_BUILD_DIR.glob(f"{context.platform}-testbed.*")
        ])

    for path in paths:
        delete_path(path)