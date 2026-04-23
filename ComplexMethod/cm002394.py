def sort_auto_mapping(fname: str, overwrite: bool = False) -> bool | None:
    """
    Sort all auto mappings in a file.

    Args:
        fname (`str`): The name of the file where we want to sort auto-mappings.
        overwrite (`bool`, *optional*, defaults to `False`): Whether or not to fix and overwrite the file.

    Returns:
        `Optional[bool]`: Returns `None` if `overwrite=True`. Otherwise returns `True` if the file has an auto-mapping
        improperly sorted, `False` if the file is okay.
    """
    with open(fname, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    line_idx = 0
    while line_idx < len(lines):
        if _re_intro_mapping.search(lines[line_idx]) is not None:
            # Start of a new mapping!
            indent = len(re.search(r"^(\s*)\S", lines[line_idx]).groups()[0]) + 8
            while not lines[line_idx].startswith(" " * indent + "("):
                new_lines.append(lines[line_idx])
                line_idx += 1

            blocks = []
            while lines[line_idx].strip() != "]":
                # Blocks either fit in one line or not
                if lines[line_idx].strip() == "(":
                    start_idx = line_idx
                    while not lines[line_idx].startswith(" " * indent + ")"):
                        line_idx += 1
                    blocks.append("\n".join(lines[start_idx : line_idx + 1]))
                else:
                    blocks.append(lines[line_idx])
                line_idx += 1

            # Sort blocks by their identifiers
            blocks = sorted(blocks, key=lambda x: _re_identifier.search(x).groups()[0])
            new_lines += blocks
        else:
            new_lines.append(lines[line_idx])
            line_idx += 1

    if overwrite:
        with open(fname, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))
    else:
        return "\n".join(new_lines) != content