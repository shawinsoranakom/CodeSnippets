def _make_block(pf: PythonFile, begin: int) -> Block:
    name = docstring = ""
    end = 0

    for i in range(begin + 1, len(pf.tokens)):
        t = pf.tokens[i]
        if not name and t.type == token.NAME:
            name = t.string
        elif not end:
            if t.type == token.INDENT:
                end = pf.indent_to_dedent[i]
                while is_empty(pf.tokens[end := end - 1]):
                    pass
            elif t.string == "...":
                end = i
        elif t.type == token.STRING:
            docstring = t.string
            break
        elif not is_empty(t):
            break

    category = Block.Category[pf.tokens[begin].string.upper()]
    return Block(
        begin=begin,
        category=category,
        docstring=docstring,
        end=end,
        name=name,
        tokens=pf.tokens,
    )