def normalize_list_like_lines(generation):
    """
    Normalize lines in the given text that resemble list items. The function looks for lines that start optionally with
    '-' or '*', possibly followed by Roman numerals or digits indicating nesting levels. The function reformats such
    lines to make them more structured.

    Args:
        generation (str): The input text containing lines that need to be normalized.

    Returns:
        str: The input text with the list-like lines normalized.

    Note:
        The function uses regular expressions to identify and reformat the list-like lines. The patterns capture
        optional bullet points, nesting levels indicated by numerals, and the actual list item content. The
        normalization adjusts the bullet point style and nesting levels based on the captured patterns.
    """

    lines = generation.split("\n")
    output_lines = []
    for line_no, line in enumerate(lines):
        match = re.search(r". ([-*]) ", line)
        if not match or line[0] not in ("-", "*"):
            output_lines.append(line)
            continue  # Doesn't fit the pattern we want, no changes
        delim = match.group(1) + " "
        splits = line.split(delim)[1:]
        replacement = ""
        delim1 = line[0] + " "

        for i, item in enumerate(splits):
            level = 0
            potential_numeral, _, rest = item.strip().partition(" ")
            if not rest:
                continue
            # Infer current nesting level based on detected numbering
            if re.match(r"^[\dixv]+((?:\.[\dixv])?)+$", potential_numeral, flags=re.IGNORECASE | re.MULTILINE):
                level = potential_numeral.count(".")

            replacement += (
                ("\n" if i > 0 else "") + ("\t" * level) + (delim if i > 0 or line_no == 0 else delim1) + item.strip()
            )

        if line_no == len(lines) - 1:  # If this is the last line in the generation
            replacement += "\n"  # Add an empty line to the end of the generation

        output_lines.append(replacement)

    return "\n".join(output_lines)