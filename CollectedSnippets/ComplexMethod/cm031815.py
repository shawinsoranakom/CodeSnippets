def tokenize(src: str, line: int = 1, filename: str = "") -> Iterator[Token]:
    linestart = -1
    for m in matcher.finditer(src):
        start, end = m.span()
        macro_body = ""
        text = m.group(0)
        if text in keywords:
            kind = keywords[text]
        elif text in annotations:
            kind = ANNOTATION
        elif letter.match(text):
            kind = IDENTIFIER
        elif text == "...":
            kind = ELLIPSIS
        elif text == ".":
            kind = PERIOD
        elif text[0] in "0123456789.":
            kind = NUMBER
        elif text[0] == '"':
            kind = STRING
        elif text in opmap:
            kind = opmap[text]
        elif text == "\n":
            linestart = start
            line += 1
            kind = "\n"
        elif text[0] == "'":
            kind = CHARACTER
        elif text[0] == "#":
            macro_body = text[1:].strip()
            if macro_body.startswith("if"):
                kind = CMACRO_IF
            elif macro_body.startswith("else"):
                kind = CMACRO_ELSE
            elif macro_body.startswith("endif"):
                kind = CMACRO_ENDIF
            else:
                kind = CMACRO_OTHER
        elif text[0] == "/" and text[1] in "/*":
            kind = COMMENT
        else:
            lineend = src.find("\n", start)
            if lineend == -1:
                lineend = len(src)
            raise make_syntax_error(
                f"Bad token: {text}",
                filename,
                line,
                start - linestart + 1,
                src[linestart:lineend],
            )
        if kind == COMMENT:
            begin = line, start - linestart
            newlines = text.count("\n")
            if newlines:
                linestart = start + text.rfind("\n")
                line += newlines
        else:
            begin = line, start - linestart
            if macro_body:
                linestart = end
                line += 1
        if kind != "\n":
            yield Token(
                filename, kind, text, begin, (line, start - linestart + len(text))
            )