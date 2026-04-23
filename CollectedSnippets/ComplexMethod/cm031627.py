def build(context: argparse.Namespace, host: str | None = None) -> None:
    """The implementation of the "build" command."""
    if host is None:
        host = context.host

    if context.clean:
        clean(context, host)

    if host in {"all", "build"}:
        for step in [
            configure_build_python,
            make_build_python,
        ]:
            step(context)

    if host == "build":
        hosts = []
    elif host in {"all", "hosts"}:
        hosts = all_host_triples(context.platform)
    else:
        hosts = [host]

    for step_host in hosts:
        for step in [
            configure_host_python,
            make_host_python,
        ]:
            step(context, host=step_host)

    if host == "all":
        package(context)