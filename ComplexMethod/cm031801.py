def escaping_call_in_simple_stmt(stmt: SimpleStmt, result: dict[SimpleStmt, EscapingCall]) -> None:
    tokens = stmt.contents
    for idx, tkn in enumerate(tokens):
        try:
            next_tkn = tokens[idx+1]
        except IndexError:
            break
        if next_tkn.kind != lexer.LPAREN:
            continue
        if tkn.kind == lexer.IDENTIFIER:
            if tkn.text.upper() == tkn.text:
                # simple macro
                continue
            #if not tkn.text.startswith(("Py", "_Py", "monitor")):
            #    continue
            if tkn.text.startswith(("sym_", "optimize_", "PyJitRef")):
                # Optimize functions
                continue
            if tkn.text.endswith("Check"):
                continue
            if tkn.text.startswith("Py_Is"):
                continue
            if tkn.text.endswith("CheckExact"):
                continue
            if tkn.text in NON_ESCAPING_FUNCTIONS:
                continue
        elif tkn.kind == "RPAREN":
            prev = tokens[idx-1]
            if prev.text.endswith("_t") or prev.text == "*" or prev.text == "int":
                #cast
                continue
        elif tkn.kind != "RBRACKET":
            continue
        if tkn.text in ("PyStackRef_CLOSE", "PyStackRef_XCLOSE"):
            if len(tokens) <= idx+2:
                raise analysis_error("Unexpected end of file", next_tkn)
            kills = tokens[idx+2]
            if kills.kind != "IDENTIFIER":
                raise analysis_error(f"Expected identifier, got '{kills.text}'", kills)
        else:
            kills = None
        result[stmt] = EscapingCall(stmt, tkn, kills)