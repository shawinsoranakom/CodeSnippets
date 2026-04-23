def add_assertions(val):
                    call_backs: list[Callable] = []
                    messages: list[str] = []
                    if isinstance(val, (torch.SymInt, torch.SymFloat, torch.SymBool)):
                        symbol = val.node.expr
                        if symbol in self.existing_inline_assertions:
                            return call_backs, messages
                        if isinstance(symbol, sympy.Symbol) and free_unbacked_symbols(
                            symbol
                        ):
                            if symbol in self._asserts_generated_unbacked_symbols:
                                return call_backs, messages
                            # We only care about unbacked symints for these inline
                            # constraints, which are prefixed with 'u'
                            constraint = self.range_constraints[symbol]
                            min_val, max_val = _convert_range_to_int(constraint)
                            assert_msg = f" is outside of inline constraint [{min_val}, {max_val}]."
                            call_backs.append(
                                partial(
                                    self._assert_range_constraint,
                                    lower=min_val,
                                    upper=max_val,
                                )
                            )
                            messages.append(assert_msg)
                            self._asserts_generated_unbacked_symbols.add(symbol)

                    elif isinstance(val, torch.Tensor):
                        for i, sym in enumerate(val.shape):
                            cbs, msgs = add_assertions(sym)
                            for cb, msg in zip(cbs, msgs):

                                def sym_size_cb(node, assert_msg, dim):
                                    with node.graph.inserting_after(node):
                                        dim_node = module.graph.call_function(
                                            torch.ops.aten.sym_size.int,
                                            (node, dim),
                                            {},
                                        )
                                    cb(node=dim_node, assert_msg=assert_msg)

                                call_backs.append(partial(sym_size_cb, dim=i))
                                messages.append(f".shape[{i}]" + msg)
                    return call_backs, messages