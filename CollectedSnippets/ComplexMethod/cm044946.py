def _parse_integration_options(integration: Any, raw_options: str) -> dict[str, Any] | None:
    """Parse --integration-options string into a dict matching the integration's declared options.

    Returns ``None`` when no options are provided.
    """
    import shlex
    parsed: dict[str, Any] = {}
    tokens = shlex.split(raw_options)
    declared_options = list(integration.options())
    declared = {opt.name.lstrip("-"): opt for opt in declared_options}
    allowed = ", ".join(sorted(opt.name for opt in declared_options))
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token.startswith("-"):
            console.print(f"[red]Error:[/red] Unexpected integration option value '{token}'.")
            if allowed:
                console.print(f"Allowed options: {allowed}")
            raise typer.Exit(1)
        name = token.lstrip("-")
        value: str | None = None
        # Handle --name=value syntax
        if "=" in name:
            name, value = name.split("=", 1)
        opt = declared.get(name)
        if not opt:
            console.print(f"[red]Error:[/red] Unknown integration option '{token}'.")
            if allowed:
                console.print(f"Allowed options: {allowed}")
            raise typer.Exit(1)
        key = name.replace("-", "_")
        if opt.is_flag:
            if value is not None:
                console.print(f"[red]Error:[/red] Option '{opt.name}' is a flag and does not accept a value.")
                raise typer.Exit(1)
            parsed[key] = True
            i += 1
        elif value is not None:
            parsed[key] = value
            i += 1
        elif i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
            parsed[key] = tokens[i + 1]
            i += 2
        else:
            console.print(f"[red]Error:[/red] Option '{opt.name}' requires a value.")
            raise typer.Exit(1)
    return parsed or None