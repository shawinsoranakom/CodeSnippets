def update_file_with_new_docstrings(
    candidate_file,
    lines,
    decorated_items: list[DecoratedItem],
    source: str,
    overwrite=False,
):
    """
    For a given file, update the docstrings for all @auto_docstring candidates and write the new content.
    """
    if not decorated_items:
        return [], [], []

    missing_docstring_args_warnings = []
    fill_docstring_args_warnings = []
    docstring_args_ro_remove_warnings = []

    # Build new file content by processing decorated items and unchanged sections
    content_base_file_new_lines = []
    last_line_added = 0  # Track the last line we've already added to output (0-based)

    for index, item in enumerate(decorated_items):
        def_line_0 = item.def_line - 1  # Convert to 0-based

        # Parse custom_args if present
        custom_args_dict = {}
        if item.custom_args_text:
            custom_args_dict, _ = parse_docstring(item.custom_args_text)

        # Generate new docstring based on kind
        if item.kind == "function":
            (
                new_docstring,
                sig_line_end,
                docstring_end,
                missing_docstring_args,
                fill_docstring_args,
                docstring_args_ro_remove,
            ) = generate_new_docstring_for_function(lines, item, custom_args_dict)
        else:  # class
            (
                new_docstring,
                sig_line_end,
                docstring_end,
                missing_docstring_args,
                fill_docstring_args,
                docstring_args_ro_remove,
            ) = generate_new_docstring_for_class(lines, item, custom_args_dict, source)

        # If sig_line_end is None, this item couldn't be processed (e.g., class with no __init__)
        # In this case, we don't modify anything and just continue to the next item
        if sig_line_end is None:
            continue

        # Add all lines from last processed line up to current def line
        content_base_file_new_lines += lines[last_line_added:def_line_0]

        # Collect warnings
        for arg in missing_docstring_args:
            missing_docstring_args_warnings.append(f"    - {arg} line {def_line_0}")
        for arg in fill_docstring_args:
            fill_docstring_args_warnings.append(f"    - {arg} line {def_line_0}")
        for arg in docstring_args_ro_remove:
            docstring_args_ro_remove_warnings.append(f"    - {arg} line {def_line_0}")

        # Add lines from current def through signature
        content_base_file_new_lines += lines[def_line_0:sig_line_end]

        # Add new docstring if generated
        if new_docstring:
            content_base_file_new_lines += new_docstring.split("\n")

        # Update last_line_added to skip the old docstring
        last_line_added = (docstring_end + 1) if docstring_end is not None else sig_line_end

    # Add any remaining lines after the last decorated item
    content_base_file_new_lines += lines[last_line_added:]

    content_base_file_new = "\n".join(content_base_file_new_lines)
    if overwrite:
        with open(candidate_file, "w", encoding="utf-8") as f:
            f.write(content_base_file_new)

    return (
        missing_docstring_args_warnings,
        fill_docstring_args_warnings,
        docstring_args_ro_remove_warnings,
    )