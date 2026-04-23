def call(self, graph_module) -> PassResult:
        self.existing_inline_assertions = _get_existing_inline_assertions(
            graph_module, self.range_constraints
        )

        for module in graph_module.modules():
            if not isinstance(module, torch.fx.GraphModule):
                continue
            for node in module.graph.nodes:
                if node.op != "call_function":
                    continue
                if "val" not in node.meta:
                    continue

                val = node.meta["val"]
                # In general, we may have to deal the case such as: ret[1].shape[0].
                # We need first find out what symbols require assertion, then we need to follow the path
                # from ret to the symbol, construct the proxies along the way and construct the messages
                # piece-wise at the same time.
                #
                # We use post-order traversal to collect all the proxies callbacks needed, construct
                # the error message callbacks, and at the top-level traversal tree we execute all the callbacks.
                # We need the callbacks because, in order to call the function to create a proxy for shape[0], we
                # need the proxy for shape, which further requires the proxy for ret[1], etc.

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

                callbacks, messages = add_assertions(val)
                for cb, msg in zip(callbacks, messages):
                    cb(node=node, assert_msg=f"{node}" + msg)

            module.recompile()

        # Sometimes this pass would return a wrong graph where we have mismatched
        # node names in signature. Before we fix it, let's just skip it.
        if (
            self.counter == 0
            and type(self) is _AddRuntimeAssertionsForInlineConstraintsPass
        ):
            return PassResult(graph_module, False)

        # Populate the stack trace with dummy vals to respect IR
        for node in graph_module.graph.nodes:
            if not node.meta.get("stack_trace", None) and node.op not in [
                "placeholder",
                "output",
            ]:
                node.meta["stack_trace"] = "".join(traceback.format_stack(limit=1))
        return PassResult(graph_module, True)