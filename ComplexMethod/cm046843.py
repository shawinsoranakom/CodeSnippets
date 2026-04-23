def visit(node: ast.AST) -> None:
        for attr in ("body", "orelse", "finalbody"):
            value = getattr(node, attr, None)
            if not isinstance(value, list) or len(value) <= 1:
                continue
            for stmt in value:
                if isinstance(stmt, ast.Pass):
                    redundant.append(stmt)
            for stmt in value:
                if isinstance(stmt, ast.AST):
                    visit(stmt)
        handlers = getattr(node, "handlers", None)
        if handlers:
            for handler in handlers:
                visit(handler)