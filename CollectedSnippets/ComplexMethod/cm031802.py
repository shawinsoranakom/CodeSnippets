def always_exits(op: parser.CodeDef) -> bool:
    depth = 0
    tkn_iter = iter(op.tokens)
    for tkn in tkn_iter:
        if tkn.kind == "LBRACE":
            depth += 1
        elif tkn.kind == "RBRACE":
            depth -= 1
        elif depth > 1:
            continue
        elif tkn.kind == "GOTO" or tkn.kind == "RETURN":
            return True
        elif tkn.kind == "KEYWORD":
            if tkn.text in EXITS:
                return True
        elif tkn.kind == "IDENTIFIER":
            if tkn.text in EXITS:
                return True
            if tkn.text == "DEOPT_IF" or tkn.text == "ERROR_IF":
                next(tkn_iter)  # '('
                t = next(tkn_iter)
                if t.text in ("true", "1"):
                    return True
    return False