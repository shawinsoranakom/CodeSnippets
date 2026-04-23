def sym_sum(self, args: list[SymNode]) -> SymNode:
        import sympy

        # Inner impl
        from torch.fx.experimental.proxy_tensor import (
            get_proxy_mode,
            handle_sym_dispatch,
        )

        if get_proxy_mode():
            return to_node(
                self,
                handle_sym_dispatch(
                    torch.sym_sum,
                    (tuple(wrap_node(a) for a in args),),
                    {},
                ),
            )
        exprs = [a.expr for a in args]
        out = sympy.Add(*exprs)

        size_hints = []
        out_hint: object = _NO_HINT
        for a in args:
            if a.hint is None:
                break
            size_hints.append(a.hint)
        else:
            out_hint = sum(size_hints)  # pyrefly: ignore[no-matching-overload]

        if self.shape_env is None:
            raise RuntimeError("shape_env is required for sym_sum")
        fx_node, _ = self.shape_env._create_fx_call_function(
            torch.sym_sum, (tuple(a.fx_node for a in args),)
        )

        # NB: Only for integers!
        return SymNode(out, self.shape_env, int, out_hint, fx_node=fx_node)