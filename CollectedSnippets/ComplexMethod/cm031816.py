def to_text(tkns: list[Token], dedent: int = 0) -> str:
    res: list[str] = []
    line, col = -1, 1 + dedent
    for tkn in tkns:
        if line == -1:
            line, _ = tkn.begin
        l, c = tkn.begin
        # assert(l >= line), (line, txt, start, end)
        while l > line:
            line += 1
            res.append("\n")
            col = 1 + dedent
        res.append(" " * (c - col))
        text = tkn.text
        if dedent != 0 and tkn.kind == "COMMENT" and "\n" in text:
            if dedent < 0:
                text = text.replace("\n", "\n" + " " * -dedent)
            # TODO: dedent > 0
        res.append(text)
        line, col = tkn.end
    return "".join(res)