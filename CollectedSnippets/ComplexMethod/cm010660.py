def build_Subscript(ctx, expr):
        def build_SliceExpr(ctx, base, slice_expr):
            lower = (
                build_expr(ctx, slice_expr.lower)
                if slice_expr.lower is not None
                else None
            )
            upper = (
                build_expr(ctx, slice_expr.upper)
                if slice_expr.upper is not None
                else None
            )
            step = (
                build_expr(ctx, slice_expr.step)
                if slice_expr.step is not None
                else None
            )
            return SliceExpr(base.range(), lower, upper, step)

        def build_Index(ctx, base, index_expr):
            if isinstance(index_expr.value, ast.Tuple):
                raise NotSupportedError(
                    base.range(),
                    "slicing multiple dimensions with tuples not supported yet",
                )
            return build_expr(ctx, index_expr.value)

        def build_ExtSlice(ctx, base, extslice):
            sub_exprs = []
            for expr in extslice.dims:
                sub_type = type(expr)
                if sub_type is ast.Index:
                    sub_exprs.append(build_Index(ctx, base, expr))
                elif sub_type is ast.Slice:
                    sub_exprs.append(build_SliceExpr(ctx, base, expr))
                elif sub_type is ast.Constant and expr.value is Ellipsis:
                    sub_exprs.append(Dots(base.range()))
                else:
                    raise NotSupportedError(
                        base.range(),
                        f"slicing multiple dimensions with {sub_type} not supported",
                    )
            return sub_exprs

        base = build_expr(ctx, expr.value)
        sub_type = type(expr.slice)
        if sub_type is ast.Index:
            if isinstance(expr.slice.value, ast.Tuple):
                # N-dimensional indexing using Tuple: x[(i, j, k)] is equivalent to x[i, j, k]
                # XXX: Indexing using a list is **different**! It triggers advanced indexing.
                indices = [
                    build_expr(ctx, index_expr) for index_expr in expr.slice.value.elts
                ]
                if not indices:
                    # `col_offset` is an int, but `end_col_offset` is
                    # `Optional[int]`. The magic number is here to make
                    # sure we can parse `()` on any machine
                    r = ctx.make_range(
                        expr.lineno,
                        expr.slice.value.col_offset,
                        expr.slice.value.col_offset + 2,
                    )
                    tup = TupleLiteral(r, [])
                    indices.append(tup)
                return Subscript(base, indices)
            else:
                return Subscript(base, [build_expr(ctx, expr.slice.value)])
        elif sub_type is ast.Slice:
            return Subscript(base, [build_SliceExpr(ctx, base, expr.slice)])
        elif sub_type is ast.ExtSlice:
            return Subscript(base, build_ExtSlice(ctx, base, expr.slice))
        else:  # In Python3.9 array indices are not wrapped in ast.Index
            if sub_type is ast.Tuple:
                # N-dimensional indexing using Tuple: x[(i, j, k)] is equivalent to x[i, j, k]
                indices = []
                for index_expr in expr.slice.elts:
                    if isinstance(index_expr, ast.Slice):
                        indices.append(build_SliceExpr(ctx, base, index_expr))
                    else:
                        indices.append(build_expr(ctx, index_expr))
                # Special-case logic for `typing.Tuple[()]`
                if not indices:
                    # See note above r.e. magic number
                    r = ctx.make_range(
                        expr.lineno, expr.slice.col_offset, expr.slice.col_offset + 2
                    )
                    tup = TupleLiteral(r, [])
                    indices.append(tup)
                return Subscript(base, indices)
            return Subscript(base, [build_expr(ctx, expr.slice)])