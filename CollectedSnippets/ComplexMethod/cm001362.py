def prompt_float(
    console: Console,
    label: str,
    description: str = "",
    default: float | None = None,
    env_var: str = "",
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    """Prompt for float input with Rich styling.

    Args:
        console: Rich Console instance
        label: Setting name/label
        description: Help text for the setting
        default: Default value
        env_var: Environment variable name
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Float value or None if empty
    """
    header = Text()
    header.append(f"{label}\n", style="bold cyan")
    if description:
        header.append(f"{description}\n", style="dim")
    if env_var:
        header.append(f"ENV: {env_var}\n", style="dim italic")

    constraints = []
    if min_value is not None:
        constraints.append(f"min: {min_value}")
    if max_value is not None:
        constraints.append(f"max: {max_value}")
    if constraints:
        header.append(f"({', '.join(constraints)})", style="dim")

    console.print()
    console.print(Panel(header, border_style="cyan", padding=(0, 1)))

    prompt_text = "Value"
    if default is not None:
        prompt_text += f" [{default}]"
    else:
        prompt_text += " [empty to skip]"

    while True:
        result = Prompt.ask(f"  {prompt_text}", console=console)

        # Handle empty input
        if not result.strip():
            return default

        # Try to parse as float
        try:
            value = float(result)

            # Validate range
            if min_value is not None and value < min_value:
                console.print(f"  [red]Value must be at least {min_value}[/red]")
                continue
            if max_value is not None and value > max_value:
                console.print(f"  [red]Value must be at most {max_value}[/red]")
                continue

            return value
        except ValueError:
            console.print("  [red]Please enter a valid number[/red]")