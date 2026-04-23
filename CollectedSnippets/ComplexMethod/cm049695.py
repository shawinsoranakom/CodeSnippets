def _patch_generator(new_content, old_content):
    """Generate a patch (multiple operations) between two contents.
    Each operation is a string with the following format:
    <operation_type>@<start_index>[,<end_index>][:<patch_text>*]
    patch format example:
        +@4:<p>ab</p><p>cd</p>
        +@4,15:<p>ef</p><p>gh</p>
        -@32
        -@125,129
        R@523:<b>sdf</b>

    :param string new_content: the new content
    :param string old_content: the old content

    :return: string: the patch containing all the operations to reverse
                     the new content to the old content
    """
    # remove break line in contents to ensure they don't interfere with
    # operations
    new_content = new_content.replace("\n", "")
    old_content = old_content.replace("\n", "")

    new_content_lines = new_content.split(LINE_SEPARATOR)
    old_content_lines = old_content.split(LINE_SEPARATOR)

    for group in SequenceMatcher(
        None, new_content_lines, old_content_lines, False
    ).get_grouped_opcodes(0):
        patch_content_line = []
        first, last = group[0], group[-1]
        patch_operation = _format_line_index(first[1], last[2])

        if any(tag in {"replace", "delete"} for tag, _, _, _, _ in group):
            for tag, _, _, _, _ in group:
                if tag not in {"insert", "equal", "replace"}:
                    patch_operation = PATCH_OPERATIONS[tag] + patch_operation

        if any(tag in {"replace", "insert"} for tag, _, _, _, _ in group):
            for tag, _, _, j1, j2 in group:
                if tag not in {"delete", "equal"}:
                    patch_operation = PATCH_OPERATIONS[tag] + patch_operation
                    for line in old_content_lines[j1:j2]:
                        patch_content_line.append(line)

        if patch_content_line:
            patch_content = LINE_SEPARATOR + LINE_SEPARATOR.join(
                patch_content_line
            )
            yield str(patch_operation) + PATCH_OPERATION_CONTENT + patch_content
        else:
            yield str(patch_operation)