def strip_local_api_network_args(extra_cli_args: Sequence[str]) -> tuple[str, ...]:
    remaining_args: list[str] = []
    i = 0

    while i < len(extra_cli_args):
        arg = extra_cli_args[i]
        if arg == "--host":
            next_index = i + 1
            if next_index < len(extra_cli_args) and not extra_cli_args[next_index].startswith("--"):
                i += 2
            else:
                i += 1
            continue

        if arg == "--port":
            next_index = i + 1
            if next_index < len(extra_cli_args) and not extra_cli_args[next_index].startswith("--"):
                i += 2
            else:
                i += 1
            continue

        if arg.startswith("--host="):
            i += 1
            continue

        if arg.startswith("--port="):
            i += 1
            continue

        remaining_args.append(arg)
        i += 1

    return tuple(remaining_args)