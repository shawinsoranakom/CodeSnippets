def reformat_paragraph(data, limit):
    """Return data reformatted to specified width (limit)."""
    lines = data.split("\n")
    i = 0
    n = len(lines)
    while i < n and is_all_white(lines[i]):
        i = i+1
    if i >= n:
        return data
    indent1 = get_indent(lines[i])
    if i+1 < n and not is_all_white(lines[i+1]):
        indent2 = get_indent(lines[i+1])
    else:
        indent2 = indent1
    new = lines[:i]
    partial = indent1
    while i < n and not is_all_white(lines[i]):
        # XXX Should take double space after period (etc.) into account
        words = re.split(r"(\s+)", lines[i])
        for j in range(0, len(words), 2):
            word = words[j]
            if not word:
                continue # Can happen when line ends in whitespace
            if len((partial + word).expandtabs()) > limit and \
                   partial != indent1:
                new.append(partial.rstrip())
                partial = indent2
            partial = partial + word + " "
            if j+1 < len(words) and words[j+1] != " ":
                partial = partial + " "
        i = i+1
    new.append(partial.rstrip())
    # XXX Should reformat remaining paragraphs as well
    new.extend(lines[i:])
    return "\n".join(new)