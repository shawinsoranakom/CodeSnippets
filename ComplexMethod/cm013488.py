def binary_magic_impl(self: SymNode, other: SymNode) -> SymNode:
        from torch.fx.experimental.proxy_tensor import (
            get_proxy_mode,
            handle_sym_dispatch,
        )

        op = method_to_operator(method)

        out_hint: object = _NO_HINT
        if self.hint is not None and other.hint is not None:
            out_hint = op(self.hint, other.hint)

        if get_proxy_mode():
            return to_node(
                self, handle_sym_dispatch(op, (wrap_node(self), wrap_node(other)), {})
            )
        if not isinstance(other, SymNode):
            raise AssertionError(f"Expected SymNode, got {type(other)}")
        optimized_summation = False
        try:
            if method == "mod":
                from torch.utils._sympy.functions import Mod, PythonMod

                # Special handling for mod that requires access to the value
                # ranges
                shape_env = self.shape_env
                if shape_env is None:
                    raise AssertionError("shape_env is required for mod")
                if (
                    self.expr.is_nonnegative
                    or shape_env.bound_sympy(self.expr).lower >= 0
                ) and (
                    other.expr.is_nonnegative
                    or shape_env.bound_sympy(other.expr).lower >= 0
                ):
                    out = Mod(self.expr, other.expr)
                else:
                    out = PythonMod(self.expr, other.expr)
            elif method == "add":
                # see Note [optimized_summation]
                (optimized_summation, out) = _optimized_add(
                    self.expr,
                    other.expr,
                    self._optimized_summation,
                    other._optimized_summation,
                )
            elif method in ("eq", "ne", "ge", "gt", "le", "lt"):
                import sympy

                from torch.utils._sympy.symbol import symbol_is_type, SymT

                # Optimization: when one side is a single unbacked symbol
                # and other is constant, use evaluate=False to skip expensive
                # relational evaluation. We only do this for unbacked symbols
                # because they have no assumptions (like positive=True) that
                # sympy would use during evaluation.
                lhs_is_unbacked = self.expr.is_symbol and symbol_is_type(
                    self.expr, SymT.UNBACKED_INT
                )
                rhs_is_unbacked = other.expr.is_symbol and symbol_is_type(
                    other.expr, SymT.UNBACKED_INT
                )
                if (lhs_is_unbacked and other.expr.is_number) or (
                    rhs_is_unbacked and self.expr.is_number
                ):
                    rel_class = {
                        "eq": sympy.Eq,
                        "ne": sympy.Ne,
                        "ge": sympy.Ge,
                        "gt": sympy.Gt,
                        "le": sympy.Le,
                        "lt": sympy.Lt,
                    }[method]
                    out = rel_class(self.expr, other.expr, evaluate=False)
                else:
                    out = func(self.expr, other.expr)

            else:
                # TODO: consider constant prop here
                out = func(self.expr, other.expr)
        except Exception:
            log.warning("failed to eval %s(%s, %s)", method, self.expr, other.expr)
            raise
        sym_node_log.debug("%s %s %s -> %s", method, self.expr, other.expr, out)
        pytype: type
        # This is not strictly correct. In Python, a**b may return complex when
        # a < 0 and b is a float: (-1)**2.1. Same for sympy.sqrt(-3.14). This
        # returns a float while both arguments are ints: 2**(-1). Also, max and
        # min do not type promote. To avoid having data-dependent control flow
        # here, we just set the type to float if one of the args is a float. In
        # case of a type mismatch, we assume that it will be detected during
        # evaluation.
        if method in always_float_magic_methods:
            pytype = float
        elif method in always_bool_magic_methods:
            pytype = bool
        elif self.pytype is float or other.pytype is float:
            pytype = float
        else:
            pytype = self.pytype

        if (
            pytype is not None
            and out_hint is not _NO_HINT
            and out_hint is not None
            and not isinstance(out_hint, SymTypes)
        ):
            out_hint = pytype(out_hint)  # type: ignore[arg-type]

        # Create a FX node that corresponds to the operation being applied to
        # this node.
        if self.shape_env is None:
            raise RuntimeError("shape_env is required for binary op")
        fx_node, _ = self.shape_env._create_fx_call_function(
            op, (self.fx_node, other.fx_node)
        )

        result = SymNode(
            out,
            self.shape_env,
            pytype,
            out_hint,  # type: ignore[arg-type]
            fx_node=fx_node,
            optimized_summation=optimized_summation,  # see Note [optimized_summation]
        )
        return result