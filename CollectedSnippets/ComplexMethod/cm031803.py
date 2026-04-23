def stmt_escapes(stmt: Stmt) -> bool:
    if isinstance(stmt, BlockStmt):
        return stmt_list_escapes(stmt.body)
    elif isinstance(stmt, SimpleStmt):
        for tkn in stmt.contents:
            if tkn.text == "DECREF_INPUTS":
                return True
        d: dict[SimpleStmt, EscapingCall] = {}
        escaping_call_in_simple_stmt(stmt, d)
        return bool(d)
    elif isinstance(stmt, IfStmt):
        if stmt.else_body and stmt_escapes(stmt.else_body):
            return True
        return stmt_escapes(stmt.body)
    elif isinstance(stmt, MacroIfStmt):
        if stmt.else_body and stmt_list_escapes(stmt.else_body):
            return True
        return stmt_list_escapes(stmt.body)
    elif isinstance(stmt, ForStmt):
        return stmt_escapes(stmt.body)
    elif isinstance(stmt, WhileStmt):
        return stmt_escapes(stmt.body)
    else:
        assert False, "Unexpected statement type"