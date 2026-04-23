def visit(stmt: Stmt) -> None:
        nonlocal error
        if isinstance(stmt, IfStmt) or isinstance(stmt, WhileStmt):
            for tkn in stmt.condition:
                if tkn in calls:
                    error = tkn
        elif isinstance(stmt, SimpleStmt):
            in_if = 0
            tkn_iter = iter(stmt.contents)
            for tkn in tkn_iter:
                if tkn.kind == "IDENTIFIER" and tkn.text in ("DEOPT_IF", "ERROR_IF", "EXIT_IF", "HANDLE_PENDING_AND_DEOPT_IF", "AT_END_EXIT_IF"):
                    in_if = 1
                    next(tkn_iter)
                elif tkn.kind == "LPAREN":
                    if in_if:
                        in_if += 1
                elif tkn.kind == "RPAREN":
                    if in_if:
                        in_if -= 1
                elif tkn in calls and in_if:
                    error = tkn