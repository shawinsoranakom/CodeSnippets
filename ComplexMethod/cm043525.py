def apply_diffs(diffs: Dict[str, Diff], files: FilesDict) -> FilesDict:
    """
    Applies diffs to the provided files.

    Args:
    - diffs (Dict[str, Diff]): A dictionary of diffs to apply, keyed by filename.
    - files (FilesDict): The original files to which diffs will be applied.

    Returns:
    - FilesDict: The updated files after applying diffs.
    """
    files = FilesDict(files.copy())
    REMOVE_FLAG = "<REMOVE_LINE>"  # Placeholder to mark lines for removal
    for diff in diffs.values():
        if diff.is_new_file():
            # If it's a new file, create it with the content from the diff
            files[diff.filename_post] = "\n".join(
                line[1] for hunk in diff.hunks for line in hunk.lines
            )
        else:
            # Convert the file content to a dictionary of lines
            line_dict = file_to_lines_dict(files[diff.filename_pre])
            for hunk in diff.hunks:
                current_line = hunk.start_line_pre_edit
                for line in hunk.lines:
                    if line[0] == RETAIN:
                        current_line += 1
                    elif line[0] == ADD:
                        # Handle added lines
                        current_line -= 1
                        if (
                            current_line in line_dict.keys()
                            and line_dict[current_line] != REMOVE_FLAG
                        ):
                            line_dict[current_line] += "\n" + line[1]
                        else:
                            line_dict[current_line] = line[1]
                        current_line += 1
                    elif line[0] == REMOVE:
                        # Mark removed lines with REMOVE_FLAG
                        line_dict[current_line] = REMOVE_FLAG
                        current_line += 1

            # Remove lines marked for removal
            line_dict = {
                key: line_content
                for key, line_content in line_dict.items()
                if REMOVE_FLAG not in line_content
            }
            # Reassemble the file content
            files[diff.filename_post] = "\n".join(line_dict.values())
    return files