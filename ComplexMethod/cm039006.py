def _get_backends_from_return(stmts: list) -> list[str]:
    """Extract backend names from return statements in a list of statements.

    Handles starred unpacking (e.g. ``*sparse_backends``) by resolving the
    variable from assignments found in the same statement list.  When the
    variable is conditionally assigned (inside an ``if/else``), the ``else``
    branch value is used as the representative default.
    """
    # Collect variable assignments so we can resolve starred expressions.
    # For conditional assignments, last-written (else branch) wins.
    var_assigns: dict[str, list[str]] = {}
    for stmt in stmts:
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.List):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    var_assigns[target.id] = [
                        e.attr for e in stmt.value.elts if isinstance(e, ast.Attribute)
                    ]
        elif isinstance(stmt, ast.If):
            for branch in (stmt.body, stmt.orelse):
                for branch_stmt in branch:
                    if isinstance(branch_stmt, ast.Assign) and isinstance(
                        branch_stmt.value, ast.List
                    ):
                        for target in branch_stmt.targets:
                            if isinstance(target, ast.Name):
                                var_assigns[target.id] = [
                                    e.attr
                                    for e in branch_stmt.value.elts
                                    if isinstance(e, ast.Attribute)
                                ]

    for stmt in stmts:
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.List):
            backends: list[str] = []
            for e in stmt.value.elts:
                if isinstance(e, ast.Attribute):
                    backends.append(e.attr)
                elif (
                    isinstance(e, ast.Starred)
                    and isinstance(e.value, ast.Name)
                    and e.value.id in var_assigns
                ):
                    backends.extend(var_assigns[e.value.id])
            return backends
    return []