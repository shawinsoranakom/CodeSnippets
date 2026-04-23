def apply_patch(initial_content, patch):
    """Apply a patch (multiple operations) on a content.
    Each operation is a string with the following format:
    <operation_type>@<start_index>[,<end_index>][:<patch_text>*]
    patch format example:
        +@4:<p>ab</p><p>cd</p>
        +@4,15:<p>ef</p><p>gh</p>
        -@32
        -@125,129
        R@523:<b>sdf</b>

    :param string initial_content: the initial content to patch
    :param string patch: the patch to apply

    :return: string: the patched content
    """
    if not patch:
        return initial_content

    # Replace break line in initial content to ensure they don't interfere with
    # operations
    initial_content = initial_content.replace("\n", "")
    initial_content = _remove_html_attribute(
        initial_content, HTML_ATTRIBUTES_TO_REMOVE
    )

    content = initial_content.split(LINE_SEPARATOR)
    patch_operations = patch.split(OPERATION_SEPARATOR)
    # Apply operations in reverse order to preserve the indexes integrity.
    patch_operations.reverse()

    for operation in patch_operations:
        metadata, *patch_content_line = operation.split(LINE_SEPARATOR)

        metadata_split = metadata.split(PATCH_OPERATION_LINE_AT)
        operation_type = metadata_split[0]
        lines_index_range = metadata_split[1] if len(metadata_split) > 1 else ""
        # We need to remove PATCH_OPERATION_CONTENT char from lines_index_range.
        lines_index_range = lines_index_range.split(PATCH_OPERATION_CONTENT)[0]
        indexes = lines_index_range.split(",")
        start_index = int(indexes[0])
        end_index = int(indexes[1]) if len(indexes) > 1 else start_index

        # We need to insert lines from last to the first
        # to preserve the indexes integrity.
        patch_content_line.reverse()

        if end_index > start_index:
            for index in range(end_index, start_index, -1):
                if operation_type in [
                    PATCH_OPERATION_REMOVE,
                    PATCH_OPERATION_REPLACE,
                ]:
                    del content[index]

        if operation_type in [PATCH_OPERATION_ADD, PATCH_OPERATION_REPLACE]:
            for line in patch_content_line:
                content.insert(start_index + 1, line)
        if operation_type in [PATCH_OPERATION_REMOVE, PATCH_OPERATION_REPLACE]:
            del content[start_index]

    return LINE_SEPARATOR.join(content)