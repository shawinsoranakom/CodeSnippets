def get_domain_value_names(domain):
    """ Return all field name used by this domain
    eg: [
            ('id', 'in', [1, 2, 3]),
            ('field_a', 'in', parent.truc),
            ('field_b', 'in', context.get('b')),
            (1, '=', 1),
            bool(context.get('c')),
        ]
        returns {'id', 'field_a', 'field_b'}, {'parent', 'parent.truc', 'context'}

    :param domain: list(tuple) or str
    :return: set(str), set(str)
    """
    contextual_values = set()
    field_names = set()

    try:
        if isinstance(domain, list):
            for leaf in domain:
                if leaf in DOMAIN_OPERATORS or leaf in (True, False):
                    # "&", "|", "!", True, False
                    continue
                left, _operator, _right = leaf
                if isinstance(left, str):
                    field_names.add(left)
                elif left not in (1, 0):
                    # deprecate: True leaf and False leaf
                    raise ValueError()

        elif isinstance(domain, str):
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

            expr = domain.strip()
            item_ast = ast.parse(f"({expr})", mode='eval').body
            if isinstance(item_ast, ast.Name):
                # domain="other_field_domain"
                contextual_values.update(_get_expression_contextual_values(item_ast))
            else:
                extract_from_domain(item_ast)

    except ValueError:
        raise ValueError("Wrong domain formatting.") from None

    value_names = set()
    for name in contextual_values:
        if name == 'parent':
            continue
        root = name.split('.')[0]
        if root not in IGNORED_IN_EXPRESSION:
            value_names.add(name if root == 'parent' else root)
    return field_names, value_names