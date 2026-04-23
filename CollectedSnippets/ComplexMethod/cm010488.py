def go(t: object, real_t: Tensor) -> None:
                if isinstance(t, FakeTensor):
                    # NB: unconditionally overwrite
                    log.debug(
                        "maybe_propagate_real_tensors %s -> %s", id(t), id(real_t)
                    )
                    t.real_tensor = real_t
                    for s, real_s in zip(t.size(), real_t.size()):
                        go(s, real_s)  # type: ignore[arg-type]
                    for s, real_s in zip(t.stride(), real_t.stride()):
                        go(s, real_s)  # type: ignore[arg-type]
                    go(t.storage_offset(), real_t.storage_offset())  # type: ignore[arg-type]
                elif isinstance(t, py_sym_types) and free_unbacked_symbols(t):
                    if isinstance(t.node.expr, sympy.Symbol):
                        if self.shape_env is None:
                            raise AssertionError(
                                "self.shape_env must not be None for symbolic Symbol"
                            )
                        self.shape_env.set_real_tensor_prop_unbacked_vals(
                            t.node.expr, real_t
                        )
                    elif (
                        isinstance(s := t.node.expr, sympy.Eq)
                        and isinstance(s.lhs, sympy.Symbol)
                        and s.rhs == 1
                    ):
                        if self.shape_env is None:
                            raise AssertionError(
                                "self.shape_env must not be None for symbolic Eq"
                            )

                        self.shape_env.set_real_tensor_prop_unbacked_vals(s, real_t)