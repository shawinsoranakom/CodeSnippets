def prompt_for_scopes() -> list[str]:
    """Prompt for scopes interactively with a menu"""
    click.echo("\nAvailable scopes:")
    for i, scope in enumerate(AVAILABLE_SCOPES, 1):
        click.echo(f"  {i}. {scope}")

    click.echo(
        "\nSelect scopes by number (comma-separated) or enter scope names directly:"
    )
    click.echo("  Example: 1,2 or EXECUTE_GRAPH,READ_GRAPH")

    while True:
        selection = click.prompt("Scopes", type=str)
        scopes = []

        for item in selection.split(","):
            item = item.strip()
            if not item:
                continue

            # Check if it's a number
            if item.isdigit():
                idx = int(item) - 1
                if 0 <= idx < len(AVAILABLE_SCOPES):
                    scopes.append(AVAILABLE_SCOPES[idx])
                else:
                    click.echo(f"  Invalid number: {item}")
                    scopes = []
                    break
            # Check if it's a valid scope name
            elif item.upper() in AVAILABLE_SCOPES:
                scopes.append(item.upper())
            else:
                click.echo(f"  Invalid scope: {item}")
                scopes = []
                break

        if scopes:
            return scopes
        click.echo("  Please enter valid scope numbers or names.")