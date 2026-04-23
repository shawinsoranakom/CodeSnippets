def wrap_declarations(text: str, length: int = 78) -> str:
    """
    A simple-minded text wrapper for C function declarations.

    It views a declaration line as looking like this:
        xxxxxxxx(xxxxxxxxx,xxxxxxxxx)
    If called with length=30, it would wrap that line into
        xxxxxxxx(xxxxxxxxx,
                 xxxxxxxxx)
    (If the declaration has zero or one parameters, this
    function won't wrap it.)

    If this doesn't work properly, it's probably better to
    start from scratch with a more sophisticated algorithm,
    rather than try and improve/debug this dumb little function.
    """
    lines = []
    for line in text.split("\n"):
        prefix, _, after_l_paren = line.partition("(")
        if not after_l_paren:
            lines.append(line)
            continue
        in_paren, _, after_r_paren = after_l_paren.partition(")")
        if not _:
            lines.append(line)
            continue
        if "," not in in_paren:
            lines.append(line)
            continue
        parameters = [x.strip() + ", " for x in in_paren.split(",")]
        prefix += "("
        if len(prefix) < length:
            spaces = " " * len(prefix)
        else:
            spaces = " " * 4

        while parameters:
            line = prefix
            first = True
            while parameters:
                if not first and (len(line) + len(parameters[0]) > length):
                    break
                line += parameters.pop(0)
                first = False
            if not parameters:
                line = line.rstrip(", ") + ")" + after_r_paren
            lines.append(line.rstrip())
            prefix = spaces
    return "\n".join(lines)