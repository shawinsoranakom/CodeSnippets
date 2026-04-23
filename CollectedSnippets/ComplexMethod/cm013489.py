def unary_magic_impl(self: SymNode) -> SymNode:
        from torch.fx.experimental.proxy_tensor import (
            get_proxy_mode,
            handle_sym_dispatch,
        )

        op = method_to_operator(method)
        if get_proxy_mode():
            return to_node(self, handle_sym_dispatch(op, (wrap_node(self),), {}))
        # TODO: consider constant prop here
        expr = self.expr
        if self.shape_env is None:
            raise RuntimeError("shape_env is required for unary op")
        if method == "floor" or method == "ceiling":
            expr = self.shape_env._simplify_floor_div(expr)

        try:
            out = func(expr)
        except Exception:
            log.warning("failed to eval %s(%s)", method, expr)
            raise
        sym_node_log.debug("%s %s -> %s", func, expr, out)
        out_hint: object = _NO_HINT
        if self.hint is not None:
            out_hint = op(self.hint)
        pytype: type
        if method in always_int_magic_methods:
            pytype = int
        elif method in always_bool_magic_methods:
            pytype = bool
        elif method in always_float_magic_methods:
            pytype = float
        else:
            pytype = self.pytype

        fx_node, _ = self.shape_env._create_fx_call_function(op, (self.fx_node,))
        return SymNode(out, self.shape_env, pytype, out_hint, fx_node=fx_node)