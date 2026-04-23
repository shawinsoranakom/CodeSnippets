def is_copy_consistent(
    filename: str, overwrite: bool = False, buffer: dict | None = None
) -> list[tuple[str, int]] | None:
    """
    Check if the code commented as a copy in a file matches the original.

    Args:
        filename (`str`):
            The name of the file to check.
        overwrite (`bool`, *optional*, defaults to `False`):
            Whether or not to overwrite the copies when they don't match.
        buffer (`dict`, *optional*):
            The buffer used to store the previous results in order to speed up the process.

    Returns:
        `Optional[List[Tuple[str, int]]]`: If `overwrite=False`, returns the list of differences as tuples `(str, int)`
        with the name of the object having a diff and the line number where there is the first diff.
    """
    base_path = TRANSFORMERS_PATH if not filename.startswith("tests") else MODEL_TEST_PATH

    with open(filename, "r", encoding="utf-8", newline="\n") as f:
        lines = f.readlines()
    diffs = []
    line_index = 0
    # Not a for loop cause `lines` is going to change (if `overwrite=True`).
    search_re = _re_copy_warning_for_test_file if filename.startswith("tests") else _re_copy_warning
    while line_index < len(lines):
        search = search_re.search(lines[line_index])
        if search is None:
            line_index += 1
            continue

        # There is some copied code here, let's retrieve the original.
        indent, object_name, replace_pattern = search.groups()

        # Find the file lines, the object's code, and its blocks
        try:
            target_lines, theoretical_code, theoretical_code_splits = find_code_and_splits(
                object_name, base_path, buffer=buffer
            )
        except Exception as exc:
            logger.error(f"[31mError while trying to find source code for {filename}.\n\n" + str(exc) + "[0")
            return []

        # code replaced by the patterns
        theoretical_code_blocks = OrderedDict()
        for name, start, end in theoretical_code_splits:
            name = replace_code(name, replace_pattern)
            code = "".join(target_lines[start:end])
            code = replace_code(code, replace_pattern)
            theoretical_code_blocks[name] = code

        theoretical_indent = get_indent(theoretical_code)

        # `start_index` is the index of the first line (the definition header) after `# Copied from`.
        # (`indent != theoretical_indent` doesn't seem to occur so far, not sure what this case is for.)
        start_index = line_index + 1 if indent == theoretical_indent else line_index
        # enter the block body
        line_index = start_index + 1

        subcode = "\n".join(theoretical_code.split("\n")[1:])
        indent = get_indent(subcode)
        # Loop to check the observed code, stop when indentation diminishes or if we see a End copy comment.
        # We can't call `find_block_end` directly as there is sth. special `# End copy"` here.
        should_continue = True
        while line_index < len(lines) and should_continue:
            line_index += 1
            if line_index >= len(lines):
                break
            line = lines[line_index]
            # There is a special pattern `# End copy` to stop early. It's not documented cause it shouldn't really be
            # used.
            should_continue = _should_continue(line, indent) and re.search(f"^{indent}# End copy", line) is None
        # `line_index` is outside the block
        # Clean up empty lines at the end (if any).
        while len(lines[line_index - 1]) <= 1:
            line_index -= 1

        # Split the observed code into blocks
        observed_code_splits = split_code_into_blocks(lines, start_index, line_index, len(indent), backtrace=True)

        is_class = lines[start_index].startswith(f"{' ' * (len(indent) - 4)}class ")
        # sanity check
        _sanity_check_splits(theoretical_code_splits, observed_code_splits, is_class=is_class, filename=filename)

        # observed code in a structured way (a dict mapping block names to blocks' code)
        observed_code_blocks = OrderedDict()
        for name, start, end in observed_code_splits:
            code = "".join(lines[start:end])
            observed_code_blocks[name] = code

        # Below, we change some names in `theoretical_code_blocks` and `observed_code_blocks`. These mappings map the
        # original names to the modified names: this is used to restore the original order of the code blocks.
        name_mappings_1 = {k: k for k in theoretical_code_blocks}
        name_mappings_2 = {k: k for k in observed_code_blocks}

        # Update code blocks' name and content:
        #   If `"# Ignore copy"` is found in a block of the observed code:
        #     1. if it's a block only in the observed code --> add it to the theoretical code.
        #     2. if it's also in the theoretical code () --> put its content (body) to the corresponding block under the
        #        same name in the theoretical code.
        #   In both cases, we change the name to have a prefix `_ignored_` so we know if we can discard them during the
        #   comparison.
        ignored_existing_block_index = 0
        ignored_new_block_index = 0
        for name in list(observed_code_blocks.keys()):
            code = observed_code_blocks[name]
            if "# Ignore copy" in code:
                if name in theoretical_code_blocks:
                    # in the target --> just copy the content
                    del theoretical_code_blocks[name]
                    theoretical_code_blocks[f"_ignored_existing_block_{ignored_existing_block_index}"] = code
                    name_mappings_1[name] = f"_ignored_existing_block_{ignored_existing_block_index}"

                    del observed_code_blocks[name]
                    observed_code_blocks[f"_ignored_existing_block_{ignored_existing_block_index}"] = code
                    name_mappings_2[name] = f"_ignored_existing_block_{ignored_existing_block_index}"
                    ignored_existing_block_index += 1
                else:
                    # not in the target --> add it
                    theoretical_code_blocks[f"_ignored_new_block_{ignored_new_block_index}"] = code
                    name_mappings_1[f"_ignored_new_block_{ignored_new_block_index}"] = (
                        f"_ignored_new_block_{ignored_new_block_index}"
                    )

                    del observed_code_blocks[name]
                    observed_code_blocks[f"_ignored_new_block_{ignored_new_block_index}"] = code
                    name_mappings_2[name] = f"_ignored_new_block_{ignored_new_block_index}"
                    ignored_new_block_index += 1

        # Respect the original block order:
        #   1. in `theoretical_code_blocks`: the new blocks will follow the existing ones
        #   2. in `observed_code_blocks`: the original order are kept with names modified potentially. This is necessary
        #      to compute the correct `diff_index` if `overwrite=True` and there is a diff.
        theoretical_code_blocks = {
            name_mappings_1[orig_name]: theoretical_code_blocks[name_mappings_1[orig_name]]
            for orig_name in name_mappings_1
        }
        observed_code_blocks = {
            name_mappings_2[orig_name]: observed_code_blocks[name_mappings_2[orig_name]]
            for orig_name in name_mappings_2
        }

        # Ignore the blocks specified to be ignored. This is the version used to check if there is a mismatch
        theoretical_code_blocks_clean = {
            k: v
            for k, v in theoretical_code_blocks.items()
            if not (k.startswith(("_ignored_existing_block_", "_ignored_new_block_")))
        }
        theoretical_code = "".join(list(theoretical_code_blocks_clean.values()))

        # stylify `theoretical_code` before compare (this is needed only when `replace_pattern` is not empty)
        if replace_pattern:
            theoretical_code = stylify(theoretical_code)
        # Remove `\n\n` in `theoretical_code` before compare (so no empty line)
        while "\n\n" in theoretical_code:
            theoretical_code = theoretical_code.replace("\n\n", "\n")

        # Compute `observed_code` where we don't include any empty line + keep track the line index between the
        # original/processed `observed_code` so we can have the correct `diff_index`.
        idx_to_orig_idx_mapping_for_observed_code_lines = {}
        idx = -1
        orig_idx = -1
        observed_code = ""
        for name, code in observed_code_blocks.items():
            code = code.removesuffix("\n")
            for code_line in code.split("\n"):
                orig_idx += 1
                if code_line.strip() and not name.startswith(("_ignored_existing_block_", "_ignored_new_block_")):
                    idx += 1
                    observed_code += code_line + "\n"
                    idx_to_orig_idx_mapping_for_observed_code_lines[idx] = orig_idx

        # Test for a diff and act accordingly.
        diff_index = check_codes_match(observed_code, theoretical_code)
        if diff_index is not None:
            try:
                # switch to the index in the original `observed_code` (i.e. before removing empty lines)
                diff_index = idx_to_orig_idx_mapping_for_observed_code_lines[diff_index]
            except KeyError:
                raise RuntimeError(f"{filename}:L{start_index}: Error in the format")
            diffs.append([object_name, diff_index + start_index + 1])
            if overwrite:
                # `theoretical_code_to_write` is a single string but may have several lines.
                theoretical_code_to_write = stylify("".join(list(theoretical_code_blocks.values())))
                lines = lines[:start_index] + [theoretical_code_to_write] + lines[line_index:]
                # Here we treat it as a single entry in `lines`.
                line_index = start_index + 1

    if overwrite and len(diffs) > 0:
        # Warn the user a file has been modified.
        print(f"Detected changes, rewriting {filename}.")
        with open(filename, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(lines)
    return diffs