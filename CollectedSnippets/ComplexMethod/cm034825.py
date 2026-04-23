def load_pa_provider(file_path: "str | Path") -> Optional[Type]:
    """Load a ``.pa.py`` file and return the provider class it defines.

    The file is executed inside the safe sandbox.  The module is expected to
    define a class named ``Provider``; if that name is absent the first class
    with a ``create_completion`` or ``create_async_generator`` attribute is
    returned instead.

    Args:
        file_path: Path to the ``.pa.py`` file.

    Returns:
        The provider class, or ``None`` if none could be found.

    Raises:
        FileNotFoundError: If *file_path* does not exist.
        ValueError: If *file_path* does not end with ``.pa.py``.
        RuntimeError: If the file fails to execute.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PA provider file not found: {file_path}")
    if not file_path.name.endswith(".pa.py"):
        raise ValueError(f"File must have .pa.py extension: {file_path}")

    code = file_path.read_text(encoding="utf-8")
    result = execute_safe_code(code)

    if not result.success:
        raise RuntimeError(
            f"Failed to load PA provider from {file_path}:\n{result.error}"
        )

    # Prefer an explicit 'Provider' name
    provider_class = result.locals.get("Provider")
    if provider_class is not None:
        return provider_class

    # Fall back to any class that looks like a provider
    for obj in result.locals.values():
        if isinstance(obj, type) and (
            hasattr(obj, "create_completion") or hasattr(obj, "create_async_generator")
        ):
            return obj

    return None