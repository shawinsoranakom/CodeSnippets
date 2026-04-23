def is_torch_jit_ignore_context_manager(stmt) -> bool:
    # checks if the statement is torch.jit.ignore context manager
    if isinstance(stmt.items[0].context_expr, ast.Call):
        # extract torch part
        function = stmt.items[0].context_expr.func
        if isinstance(function, ast.Attribute):
            attr_name = function.attr
            attr_value = function.value
            if attr_name == "_IgnoreContextManager" and isinstance(
                attr_value, ast.Attribute
            ):
                # there should be at most two nested attributes (e.g torch.jit._IgnoreContextManager)
                if attr_value.attr == "jit" and isinstance(attr_value.value, ast.Name):
                    if attr_value.value.id == "torch":
                        return True
    return False