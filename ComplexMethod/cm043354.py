def config_set_cmd(key: str, value: str):
    """Set a configuration setting"""
    config = get_global_config()

    # Normalize key to uppercase
    key = key.upper()

    if key not in USER_SETTINGS:
        console.print(f"[red]Error: Unknown setting '{key}'[/red]")
        console.print(f"[yellow]Available settings: {', '.join(USER_SETTINGS.keys())}[/yellow]")
        return

    setting = USER_SETTINGS[key]

    # Type conversion and validation
    if setting["type"] == "boolean":
        if value.lower() in ["true", "yes", "1", "y"]:
            typed_value = True
        elif value.lower() in ["false", "no", "0", "n"]:
            typed_value = False
        else:
            console.print(f"[red]Error: Invalid boolean value. Use 'true' or 'false'.[/red]")
            return
    elif setting["type"] == "string":
        typed_value = value

        # Check if the value should be one of the allowed options
        if "options" in setting and value not in setting["options"]:
            console.print(f"[red]Error: Value must be one of: {', '.join(setting['options'])}[/red]")
            return

    # Update config
    config[key] = typed_value
    save_global_config(config)

    # Handle secret values for display
    display_value = typed_value
    if setting.get("secret", False) and typed_value:
        display_value = "********"

    console.print(f"[green]Successfully set[/green] [cyan]{key}[/cyan] = [green]{display_value}[/green]")