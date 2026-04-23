def validate_script_path(script_path: Path | str, verbose_print) -> tuple[str, Path]:
    """Validate script path or URL and return file extension and resolved path.

    Args:
        script_path: Path to the script file or URL
        verbose_print: Function to print verbose messages

    Returns:
        Tuple of (file_extension, resolved_path)

    Raises:
        typer.Exit: If validation fails
    """
    # Handle URL case
    if isinstance(script_path, str) and is_url(script_path):
        resolved_path = download_script_from_url(script_path, verbose_print)
        file_extension = resolved_path.suffix.lower()
        if file_extension != ".py":
            verbose_print(f"Error: URL must point to a Python script (.py file), got: {file_extension}")
            raise typer.Exit(1)
        return file_extension, resolved_path

    # Handle local file case
    if isinstance(script_path, str):
        script_path = Path(script_path)

    if not script_path.exists():
        verbose_print(f"Error: File '{script_path}' does not exist.")
        raise typer.Exit(1)

    if not script_path.is_file():
        verbose_print(f"Error: '{script_path}' is not a file.")
        raise typer.Exit(1)

    # Check file extension and validate
    file_extension = script_path.suffix.lower()
    if file_extension not in [".py", ".json"]:
        verbose_print(f"Error: '{script_path}' must be a .py or .json file.")
        raise typer.Exit(1)

    return file_extension, script_path