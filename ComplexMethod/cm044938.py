def merge_json_files(existing_path: Path, new_content: Any, verbose: bool = False) -> Optional[dict[str, Any]]:
    """Merge new JSON content into existing JSON file.

    Performs a polite deep merge where:
    - New keys are added
    - Existing keys are preserved (not overwritten) unless both values are dictionaries
    - Nested dictionaries are merged recursively only when both sides are dictionaries
    - Lists and other values are preserved from base if they exist

    Args:
        existing_path: Path to existing JSON file
        new_content: New JSON content to merge in
        verbose: Whether to print merge details

    Returns:
        Merged JSON content as dict, or None if the existing file should be left untouched.
    """
    # Load existing content first to have a safe fallback
    existing_content = None
    exists = existing_path.exists()

    if exists:
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                # Handle comments (JSONC) natively with json5
                # Note: json5 handles BOM automatically
                existing_content = json5.load(f)
        except FileNotFoundError:
            # Handle race condition where file is deleted after exists() check
            exists = False
        except Exception as e:
            if verbose:
                console.print(f"[yellow]Warning: Could not read or parse existing JSON in {existing_path.name} ({e}).[/yellow]")
            # Skip merge to preserve existing file if unparseable or inaccessible (e.g. PermissionError)
            return None

    # Validate template content
    if not isinstance(new_content, dict):
        if verbose:
            console.print(f"[yellow]Warning: Template content for {existing_path.name} is not a dictionary. Preserving existing settings.[/yellow]")
        return None

    if not exists:
        return new_content

    # If existing content parsed but is not a dict, skip merge to avoid data loss
    if not isinstance(existing_content, dict):
        if verbose:
            console.print(f"[yellow]Warning: Existing JSON in {existing_path.name} is not an object. Skipping merge to avoid data loss.[/yellow]")
        return None

    def deep_merge_polite(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge update dict into base dict, preserving base values."""
        result = base.copy()
        for key, value in update.items():
            if key not in result:
                # Add new key
                result[key] = value
            elif isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = deep_merge_polite(result[key], value)
            else:
                # Key already exists and values are not both dicts; preserve existing value.
                # This ensures user settings aren't overwritten by template defaults.
                pass
        return result

    merged = deep_merge_polite(existing_content, new_content)

    # Detect if anything actually changed. If not, return None so the caller
    # can skip rewriting the file (preserving user's comments/formatting).
    if merged == existing_content:
        return None

    if verbose:
        console.print(f"[cyan]Merged JSON file:[/cyan] {existing_path.name}")

    return merged