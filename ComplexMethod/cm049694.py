def generate_comparison(new_content, old_content):
    """Compare a content to an older content
    and generate a comparison html between both content.

    :param string new_content: the current content
    :param string old_content: the old content

    :return: string: the comparison content
    """
    new_content = _remove_html_attribute(new_content, HTML_ATTRIBUTES_TO_REMOVE)
    old_content = _remove_html_attribute(old_content, HTML_ATTRIBUTES_TO_REMOVE)

    if new_content == old_content:
        return new_content

    patch = generate_patch(new_content, old_content)
    comparison = new_content.split(LINE_SEPARATOR)
    patch_operations = patch.split(OPERATION_SEPARATOR)
    # We need to apply operation from last to the first
    # to preserve the indexes integrity.
    patch_operations.reverse()

    for operation in patch_operations:
        metadata, *patch_content_line = operation.split(LINE_SEPARATOR)

        metadata_split = metadata.split(PATCH_OPERATION_LINE_AT)
        operation_type = metadata_split[0]
        lines_index_range = metadata_split[1] if len(metadata_split) > 1 else ""
        lines_index_range = lines_index_range.split(PATCH_OPERATION_CONTENT)[0]
        indexes = lines_index_range.split(",")
        start_index = int(indexes[0])
        end_index = int(indexes[1]) if len(indexes) > 1 else start_index

        # If the operation is a replace, we need to flag the changes that
        # will generate ghost opening tags if we don't ignore
        # them.
        # this can append when:
        # * A change concerning only html parameters.
        #   <p class="x">a</p> => <p class="y">a</p>
        # * An addition in a previously empty element opening tag
        #   <p></p> => <p>a</p>
        if operation_type == PATCH_OPERATION_REPLACE:
            for i, line in enumerate(patch_content_line):
                current_index = start_index + i
                if current_index > end_index:
                    break

                current_line = comparison[current_index]
                current_line_tag = current_line.split(">")[0]
                line_tag = line.split(">")[0]
                if current_line[-1] == ">" and (
                    current_line_tag == line_tag
                    or current_line_tag.split(" ")[0] == line_tag.split(" ")[0]
                ):
                    comparison[start_index + i] = "delete_me>"

        # We need to insert lines from last to the first
        # to preserve the indexes integrity.
        patch_content_line.reverse()

        for index in range(end_index, start_index - 1, -1):
            if operation_type in [
                PATCH_OPERATION_REMOVE,
                PATCH_OPERATION_REPLACE,
            ]:
                deletion_flagged_comparison = re.sub(
                    HTML_TAG_ISOLATION_REGEX,
                    DELETION_COMPARISON_REGEX,
                    comparison[index],
                )
                # Only use this line if it doesn't generate an empty
                # <removed> tag
                if not re.search(
                    EMPTY_OPERATION_TAG, deletion_flagged_comparison
                ):
                    comparison[index] = deletion_flagged_comparison

        if operation_type == PATCH_OPERATION_ADD:
            for line in patch_content_line:
                addition_flagged_line = re.sub(
                    HTML_TAG_ISOLATION_REGEX, ADDITION_COMPARISON_REGEX, line
                )

                if not re.search(EMPTY_OPERATION_TAG, addition_flagged_line):
                    comparison.insert(start_index + 1, addition_flagged_line)
                else:
                    comparison.insert(start_index + 1, line)

        if operation_type == PATCH_OPERATION_REPLACE:
            for line in patch_content_line:
                addition_flagged_line = re.sub(
                    HTML_TAG_ISOLATION_REGEX, ADDITION_COMPARISON_REGEX, line
                )
                if not re.search(EMPTY_OPERATION_TAG, addition_flagged_line):
                    comparison.insert(start_index, addition_flagged_line)
                elif (
                    line.split(">")[0] != comparison[start_index].split(">")[0]
                    or line.startswith("/")
                ):
                    comparison.insert(start_index, line)

    final_comparison = LINE_SEPARATOR.join(comparison)
    # We can remove all the opening tags which are located between the end of an
    # added tag and the start of a removed tag, because this should never happen
    # as the added and removed tags should always be near each other.
    # This can happen when the new container tag had a parameter change.
    final_comparison = re.sub(
        SAME_TAG_REPLACE_FIXER, "</added><removed>", final_comparison
    )

    # Remove al the <delete_me> tags
    final_comparison = final_comparison.replace(r"<delete_me>", "")

    # This fix the issue of unnecessary replace tags.
    # ex: <added>abc</added><removed>abc</removed> -> abc
    # This can occur when the new content is the same as the old content and
    # their container tags are the same but the tags parameters are different
    for match in re.finditer(UNNECESSARY_REPLACE_FIXER, final_comparison):
        if match.group(1) == match.group(2):
            final_comparison = final_comparison.replace(
                match.group(0), match.group(1)
            )

    return final_comparison