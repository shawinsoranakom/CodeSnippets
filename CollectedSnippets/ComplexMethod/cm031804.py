def stmt_has_jump_on_unpredictable_path(stmt: Stmt, branches_seen: int) -> tuple[bool, int]:
    if isinstance(stmt, BlockStmt):
        return stmt_has_jump_on_unpredictable_path_body(stmt.body, branches_seen)
    elif isinstance(stmt, SimpleStmt):
        for tkn in stmt.contents:
            if tkn.text == "JUMPBY":
                return True, branches_seen
        return False, branches_seen
    elif isinstance(stmt, IfStmt):
        predict, seen = stmt_has_jump_on_unpredictable_path(stmt.body, branches_seen)
        if stmt.else_body:
            predict_else, seen_else = stmt_has_jump_on_unpredictable_path(stmt.else_body, branches_seen)
            return predict != predict_else, seen + seen_else + 1
        return predict, seen + 1
    elif isinstance(stmt, MacroIfStmt):
        predict, seen = stmt_has_jump_on_unpredictable_path_body(stmt.body, branches_seen)
        if stmt.else_body:
            predict_else, seen_else = stmt_has_jump_on_unpredictable_path_body(stmt.else_body, branches_seen)
            return predict != predict_else, seen + seen_else
        return predict, seen
    elif isinstance(stmt, ForStmt):
        unpredictable, branches_seen = stmt_has_jump_on_unpredictable_path(stmt.body, branches_seen)
        return unpredictable, branches_seen + 1
    elif isinstance(stmt, WhileStmt):
        unpredictable, branches_seen = stmt_has_jump_on_unpredictable_path(stmt.body, branches_seen)
        return unpredictable, branches_seen + 1
    else:
        assert False, f"Unexpected statement type {stmt}"