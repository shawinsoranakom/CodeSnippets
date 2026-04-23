def _extract_anchors_from_expr(segment: str) -> _Anchors | None:
    """
    Given source code `segment` corresponding to a bytecode
    instruction, determine:
        - for binary ops, the location of the binary op
        - for indexing, the location of the brackets.
    `segment` is expected to be a valid Python expression
    """
    assert sys.version_info >= (3, 11)

    import ast

    tree: Any | None = None
    try:
        # Without brackets, `segment` is parsed as a statement.
        # We expect an expression, so wrap `segment` in
        # brackets to handle multi-line expressions.
        tree = ast.parse("(\n" + segment + "\n)")
    except SyntaxError:
        return None
    assert tree is not None

    if len(tree.body) != 1:
        return None

    lines = segment.split("\n")

    # get character index given byte offset
    def normalize(lineno: int, offset: int) -> int:
        return _fix_offset(lines[lineno], offset)

    # Gets the next valid character index in `lines`, if
    # the current location is not valid. Handles empty lines.
    def next_valid_char(lineno: int, col: int) -> tuple[int, int]:
        while lineno < len(lines) and col >= len(lines[lineno]):
            col = 0
            lineno += 1
        assert lineno < len(lines) and col < len(lines[lineno])
        return lineno, col

    # Get the next valid character index in `lines`.
    def increment(lineno: int, col: int) -> tuple[int, int]:
        col += 1
        lineno, col = next_valid_char(lineno, col)
        assert lineno < len(lines) and col < len(lines[lineno])
        return lineno, col

    # Get the next valid character at least on the next line
    def nextline(lineno: int, col: int) -> tuple[int, int]:
        col = 0
        lineno += 1
        lineno, col = next_valid_char(lineno, col)
        assert lineno < len(lines) and col < len(lines[lineno])
        return lineno, col

    statement = tree.body[0]
    if isinstance(statement, ast.Expr):
        expr = statement.value
        if isinstance(expr, ast.BinOp):
            # ast gives locations for BinOp subexpressions, e.g.
            # ( left_expr ) + ( right_expr )
            #   left^^^^^       right^^^^^
            # -2 since end_lineno is 1-indexed and because we added an extra
            # bracket to `segment` when calling ast.parse
            cur_lineno = cast(int, expr.left.end_lineno) - 2
            assert expr.left.end_col_offset is not None
            cur_col = normalize(cur_lineno, expr.left.end_col_offset)
            cur_lineno, cur_col = next_valid_char(cur_lineno, cur_col)

            # Heuristic to find the operator character.
            # The original CPython implementation did not look for ), \, or #,
            # leading to incorrect anchor location, e.g.
            # (x) + (y)
            # ~~^~~~~~~
            while (ch := lines[cur_lineno][cur_col]).isspace() or ch in ")\\#":
                if ch in "\\#":
                    cur_lineno, cur_col = nextline(cur_lineno, cur_col)
                else:
                    cur_lineno, cur_col = increment(cur_lineno, cur_col)

            # binary op is 1 or 2 characters long, on the same line
            right_col = cur_col + 1
            if (
                right_col < len(lines[cur_lineno])
                and not (ch := lines[cur_lineno][right_col]).isspace()
                and ch not in "\\#"
            ):
                right_col += 1
            # right_col can be invalid since it is exclusive

            return _Anchors(cur_lineno, cur_col, cur_lineno, right_col)
        elif isinstance(expr, ast.Subscript):
            # ast gives locations for value and slice subexpressions, e.g.
            # ( value_expr ) [ slice_expr ]
            #   value^^^^^     slice^^^^^
            # subscript^^^^^^^^^^^^^^^^^^^^
            # find left bracket (first '[' after value)
            left_lineno = cast(int, expr.value.end_lineno) - 2
            assert expr.value.end_col_offset is not None
            left_col = normalize(left_lineno, expr.value.end_col_offset)
            left_lineno, left_col = next_valid_char(left_lineno, left_col)
            while lines[left_lineno][left_col] != "[":
                left_lineno, left_col = increment(left_lineno, left_col)
            # find right bracket (final character of expression)
            right_lineno = cast(int, expr.end_lineno) - 2
            assert expr.end_col_offset is not None
            right_col = normalize(right_lineno, expr.end_col_offset)
            return _Anchors(left_lineno, left_col, right_lineno, right_col)
        elif isinstance(expr, ast.Call):
            # ( func_expr ) (args, kwargs)
            #   func^^^^^
            # call^^^^^^^^^^^^^^^^^^^^^^^^
            # find left bracket (first '(' after func)
            left_lineno = cast(int, expr.func.end_lineno) - 2
            assert expr.func.end_col_offset is not None
            left_col = normalize(left_lineno, expr.func.end_col_offset)
            left_lineno, left_col = next_valid_char(left_lineno, left_col)
            while lines[left_lineno][left_col] != "(":
                left_lineno, left_col = increment(left_lineno, left_col)
            # find right bracket (final character of expression)
            right_lineno = cast(int, expr.end_lineno) - 2
            assert expr.end_col_offset is not None
            right_col = normalize(right_lineno, expr.end_col_offset)
            return _Anchors(left_lineno, left_col, right_lineno, right_col)

    return None