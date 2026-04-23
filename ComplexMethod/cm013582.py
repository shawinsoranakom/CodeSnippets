def _sympy_interp(expr: sympy.Expr) -> MetaProxy:
        # sympy_interp() with hash consing, and special handling for
        # generating constants correctly

        # hash cons
        if isinstance(expr, Symbol) and expr not in expr_to_tensor_proxy:
            # This is guaranteed to be populated by invariant established by
            # insert_deferred_runtime_asserts
            expr_to_tensor_proxy[expr] = torch.ops.aten.scalar_tensor.default(
                expr_to_sym_proxy[expr]
            )

        # cache constants, why not
        if isinstance(expr, (Integer, Number, BooleanAtom)):
            dtype = None
            c: bool | int | float
            if isinstance(expr, BooleanAtom):
                dtype = torch.bool
                c = bool(expr)
            elif isinstance(expr, sympy.Integer):
                dtype = torch.int64
                c = int(expr)
            elif isinstance(expr, sympy.Number):
                dtype = torch.float64
                c = float(expr)

            node = graph.call_function(
                torch.ops.aten.scalar_tensor.default,
                # pyrefly: ignore [unbound-name]
                (c,),
                {"dtype": dtype},
            )
            with fake_mode:
                # pyrefly: ignore [unbound-name]
                node.meta["val"] = torch.ops.aten.scalar_tensor.default(c, dtype=dtype)
            expr_to_tensor_proxy[expr] = MetaProxy(
                node,
                tracer=tracer,
                fake_mode=fake_mode,
            )

        if expr in expr_to_tensor_proxy:
            return expr_to_tensor_proxy[expr]

        # don't cache
        if isinstance(expr, Symbol):
            return sympy_interp(Analysis, expr_to_tensor_proxy, expr)  # type: ignore[arg-type]

        # hash cons on arguments, run expr handler
        expr_to_tensor_proxy[expr] = _run_sympy_handler(
            Analysis,
            [_sympy_interp(arg) for arg in expr.args],  # type: ignore[arg-type]
            expr,
        )

        return expr_to_tensor_proxy[expr]