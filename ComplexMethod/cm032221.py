def fix_markdown_indent(txt):
    # fix markdown indent
    if (" - " not in txt) or (". " not in txt):
        # do not need to fix, fast escape
        return txt
    # walk through the lines and fix non-standard indentation
    lines = txt.split("\n")
    pattern = re.compile(r"^\s+-")
    activated = False
    for i, line in enumerate(lines):
        if line.startswith("- ") or line.startswith("1. "):
            activated = True
        if activated and pattern.match(line):
            stripped_string = line.lstrip()
            num_spaces = len(line) - len(stripped_string)
            if (num_spaces % 4) == 3:
                num_spaces_should_be = math.ceil(num_spaces / 4) * 4
                lines[i] = " " * num_spaces_should_be + stripped_string
    return "\n".join(lines)