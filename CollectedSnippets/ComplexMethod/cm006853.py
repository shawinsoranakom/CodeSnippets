def _parse_pep723_block(script_path: Path, verbose_print) -> dict | None:
    """Extract the TOML table contained in a PEP-723 inline metadata block.

    Args:
        script_path: Path to the Python script to inspect.
        verbose_print: Diagnostic printer.

    Returns:
        Parsed TOML dict if a block is found and successfully parsed, otherwise None.
    """
    if _toml_parser is None:
        verbose_print("tomllib/tomli not available - cannot parse inline dependencies")
        return None

    try:
        lines = script_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:  # pragma: no cover
        verbose_print(f"Failed reading script for dependency parsing: {exc}")
        return None

    # Locate `# /// script` and closing `# ///` markers.
    try:
        start_idx = next(i for i, ln in enumerate(lines) if ln.lstrip().startswith("# /// script")) + 1
        end_idx = next(i for i, ln in enumerate(lines[start_idx:], start=start_idx) if ln.lstrip().startswith("# ///"))
    except StopIteration:
        return None  # No valid block

    # Remove leading comment markers and excess whitespace
    block_lines: list[str] = []
    for raw_line in lines[start_idx:end_idx]:
        stripped_line = raw_line.lstrip()
        if not stripped_line.startswith("#"):
            continue
        block_lines.append(stripped_line.lstrip("# "))

    block_toml = "\n".join(block_lines).strip()
    if not block_toml:
        return None

    try:
        return _toml_parser.loads(block_toml)
    except Exception as exc:  # pragma: no cover  # noqa: BLE001
        verbose_print(f"Failed parsing TOML from PEP-723 block: {exc}")
        return None