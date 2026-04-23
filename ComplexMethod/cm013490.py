def sizes_strides_impl(
        self: SymNode, sizes: list[SymNode], strides: list[SymNode]
    ) -> SymNode:
        from torch.fx.experimental.proxy_tensor import (
            get_proxy_mode,
            handle_sym_dispatch,
        )

        op = getattr(sys.modules[__name__], method)
        if get_proxy_mode():
            return to_node(
                self,
                handle_sym_dispatch(
                    op,
                    ([wrap_node(s) for s in sizes], [wrap_node(s) for s in strides]),
                    {},
                ),
            )
        size_exprs = [s.expr for s in sizes]
        stride_exprs = [s.expr for s in strides]
        try:
            out = func(size_exprs, stride_exprs)
        except Exception:
            log.warning("failed to eval %s(%s, %s)", method, size_exprs, stride_exprs)
            raise
        # bool is never expandable

        size_hints = []
        out_hint = None
        for s in sizes:
            if s.hint is None:
                break
            size_hints.append(s.hint)
        else:
            stride_hints = []
            for s in strides:
                if s.hint is None:
                    break
                stride_hints.append(s.hint)
            else:
                out_hint = op(size_hints, stride_hints)

        # NB: This is the indicator function, not the actual bool!
        pytype: type
        if method.endswith("_indicator"):
            pytype = int
        else:
            pytype = bool
        return SymNode(out, self.shape_env, pytype, out_hint)