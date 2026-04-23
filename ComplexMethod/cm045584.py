def validate_and_resolve_spawn_args(
    *,
    threads: int,
    processes: int | None,
    first_port: int,
    addresses: str | None,
    process_id: int | None,
) -> tuple[int, int]:
    """Validate spawn arguments and return the resolved (processes, process_id)."""
    if threads < 1:
        raise click.UsageError("--threads must be at least 1")
    if processes is not None and processes < 1:
        raise click.UsageError("--processes must be at least 1")
    if addresses is not None and processes is not None:
        raise click.UsageError(
            "--processes and --addresses are mutually exclusive: "
            "when --addresses is set, the process count is deduced from the address list"
        )
    if addresses is not None:
        if process_id is None:
            raise click.UsageError("--process-id is required when --addresses is set")
        address_list = addresses.split(",")
        for addr in address_list:
            parts = addr.split(":")
            if len(parts) != 2 or not parts[1].isdigit():
                raise click.UsageError(
                    f"invalid address {addr!r} in --addresses: expected host:port format"
                )
            port = int(parts[1])
            if not (1 <= port <= MAX_PORT):
                raise click.UsageError(
                    f"invalid port {port} in --addresses entry {addr!r}: must be in range 1..{MAX_PORT}"
                )
        if len(address_list) != len(set(address_list)):
            raise click.UsageError("--addresses contains duplicate entries")
        processes = len(address_list)
        if not (0 <= process_id < processes):
            raise click.UsageError(
                f"--process-id {process_id} is out of range: "
                f"--addresses defines {processes} process(es), valid range is 0..{processes - 1}"
            )
    else:
        if process_id is not None:
            raise click.UsageError("--process-id requires --addresses")
        process_id = 0
        processes = processes or 1
        last_port = first_port + processes - 1
        if last_port > MAX_PORT:
            raise click.UsageError(
                f"--first-port {first_port} with --processes {processes} requires "
                f"port {last_port}, which exceeds the maximum of {MAX_PORT}"
            )
    return processes, process_id