def _extract_caret_anchors_from_line_segment(segment):
    """
    Given source code `segment` corresponding to a FrameSummary, determine:
        - for binary ops, the location of the binary op
        - for indexing and function calls, the location of the brackets.
    `segment` is expected to be a valid Python expression.
    """
    import ast

    try:
        # Without parentheses, `segment` is parsed as a statement.
        # Binary ops, subscripts, and calls are expressions, so
        # we can wrap them with parentheses to parse them as
        # (possibly multi-line) expressions.
        # e.g. if we try to highlight the addition in
        # x = (
        #     a +
        #     b
        # )
        # then we would ast.parse
        #     a +
        #     b
        # which is not a valid statement because of the newline.
        # Adding brackets makes it a valid expression.
        # (
        #     a +
        #     b
        # )
        # Line locations will be different than the original,
        # which is taken into account later on.
        tree = ast.parse(f"(\n{segment}\n)")
    except SyntaxError:
        return None

    if len(tree.body) != 1:
        return None

    lines = segment.splitlines()

    def normalize(lineno, offset):
        """Get character index given byte offset"""
        return _byte_offset_to_character_offset(lines[lineno], offset)

    def next_valid_char(lineno, col):
        """Gets the next valid character index in `lines`, if
        the current location is not valid. Handles empty lines.
        """
        while lineno < len(lines) and col >= len(lines[lineno]):
            col = 0
            lineno += 1
        assert lineno < len(lines) and col < len(lines[lineno])
        return lineno, col

    def increment(lineno, col):
        """Get the next valid character index in `lines`."""
        col += 1
        lineno, col = next_valid_char(lineno, col)
        return lineno, col

    def nextline(lineno, col):
        """Get the next valid character at least on the next line"""
        col = 0
        lineno += 1
        lineno, col = next_valid_char(lineno, col)
        return lineno, col

    def increment_until(lineno, col, stop):
        """Get the next valid non-"\\#" character that satisfies the `stop` predicate"""
        while True:
            ch = lines[lineno][col]
            if ch in "\\#":
                lineno, col = nextline(lineno, col)
            elif not stop(ch):
                lineno, col = increment(lineno, col)
            else:
                break
        return lineno, col

    def setup_positions(expr, force_valid=True):
        """Get the lineno/col position of the end of `expr`. If `force_valid` is True,
        forces the position to be a valid character (e.g. if the position is beyond the
        end of the line, move to the next line)
        """
        # -2 since end_lineno is 1-indexed and because we added an extra
        # bracket + newline to `segment` when calling ast.parse
        lineno = expr.end_lineno - 2
        col = normalize(lineno, expr.end_col_offset)
        return next_valid_char(lineno, col) if force_valid else (lineno, col)

    statement = tree.body[0]
    match statement:
        case ast.Expr(expr):
            match expr:
                case ast.BinOp():
                    # ast gives these locations for BinOp subexpressions
                    # ( left_expr ) + ( right_expr )
                    #   left^^^^^       right^^^^^
                    lineno, col = setup_positions(expr.left)

                    # First operator character is the first non-space/')' character
                    lineno, col = increment_until(lineno, col, lambda x: not x.isspace() and x != ')')

                    # binary op is 1 or 2 characters long, on the same line,
                    # before the right subexpression
                    right_col = col + 1
                    if (
                        right_col < len(lines[lineno])
                        and (
                            # operator char should not be in the right subexpression
                            expr.right.lineno - 2 > lineno or
                            right_col < normalize(expr.right.lineno - 2, expr.right.col_offset)
                        )
                        and not (ch := lines[lineno][right_col]).isspace()
                        and ch not in "\\#"
                    ):
                        right_col += 1

                    # right_col can be invalid since it is exclusive
                    return _Anchors(lineno, col, lineno, right_col)
                case ast.Subscript():
                    # ast gives these locations for value and slice subexpressions
                    # ( value_expr ) [ slice_expr ]
                    #   value^^^^^     slice^^^^^
                    # subscript^^^^^^^^^^^^^^^^^^^^

                    # find left bracket
                    left_lineno, left_col = setup_positions(expr.value)
                    left_lineno, left_col = increment_until(left_lineno, left_col, lambda x: x == '[')
                    # find right bracket (final character of expression)
                    right_lineno, right_col = setup_positions(expr, force_valid=False)
                    return _Anchors(left_lineno, left_col, right_lineno, right_col)
                case ast.Call():
                    # ast gives these locations for function call expressions
                    # ( func_expr ) (args, kwargs)
                    #   func^^^^^
                    # call^^^^^^^^^^^^^^^^^^^^^^^^

                    # find left bracket
                    left_lineno, left_col = setup_positions(expr.func)
                    left_lineno, left_col = increment_until(left_lineno, left_col, lambda x: x == '(')
                    # find right bracket (final character of expression)
                    right_lineno, right_col = setup_positions(expr, force_valid=False)
                    return _Anchors(left_lineno, left_col, right_lineno, right_col)

    return None