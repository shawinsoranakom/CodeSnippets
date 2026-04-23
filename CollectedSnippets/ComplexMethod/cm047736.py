def extract_from_domain(ast_domain):
                if isinstance(ast_domain, ast.IfExp):
                    # [] if condition else []
                    extract_from_domain(ast_domain.body)
                    extract_from_domain(ast_domain.orelse)
                    return
                if isinstance(ast_domain, ast.BoolOp):
                    # condition and []
                    # this formating don't check returned domain syntax
                    for value in ast_domain.values:
                        if isinstance(value, (ast.List, ast.IfExp, ast.BoolOp, ast.BinOp)):
                            extract_from_domain(value)
                        else:
                            contextual_values.update(_get_expression_contextual_values(value))
                    return
                if isinstance(ast_domain, ast.BinOp):
                    # [] + []
                    # this formating don't check returned domain syntax
                    if isinstance(ast_domain.left, (ast.List, ast.IfExp, ast.BoolOp, ast.BinOp)):
                        extract_from_domain(ast_domain.left)
                    else:
                        contextual_values.update(_get_expression_contextual_values(ast_domain.left))

                    if isinstance(ast_domain.right, (ast.List, ast.IfExp, ast.BoolOp, ast.BinOp)):
                        extract_from_domain(ast_domain.right)
                    else:
                        contextual_values.update(_get_expression_contextual_values(ast_domain.right))
                    return
                for ast_item in ast_domain.elts:
                    if isinstance(ast_item, ast.Constant):
                        # "&", "|", "!", True, False
                        if ast_item.value not in DOMAIN_OPERATORS and ast_item.value not in (True, False):
                            raise ValueError()
                    elif isinstance(ast_item, (ast.List, ast.Tuple)):
                        left, _operator, right = ast_item.elts
                        contextual_values.update(_get_expression_contextual_values(right))
                        if isinstance(left, ast.Constant) and isinstance(left.value, str):
                            field_names.add(left.value)
                        elif isinstance(left, ast.Constant) and left.value in (1, 0):
                            # deprecate: True leaf (1, '=', 1) and False leaf (0, '=', 1)
                            pass
                        elif isinstance(right, ast.Constant) and right.value == 1:
                            # deprecate: True/False leaf (py expression, '=', 1)
                            contextual_values.update(_get_expression_contextual_values(left))
                        else:
                            raise ValueError()
                    else:
                        raise ValueError()