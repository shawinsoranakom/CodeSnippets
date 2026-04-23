def create_graph_input(
        self,
        name: str,
        type_expr: Any,
        example_value: Any,
        before: bool = False,
        source: Source | None = None,
    ) -> fx.Proxy:
        if isinstance(example_value, torch.Tensor):
            self._input_versions_at_beginning.append(example_value._version)
        log.debug(
            "create_graph_input %s %s %s at debug_level %s before=%s",
            name,
            source.name if source is not None else "(none)",
            example_value,
            self.debug_level,
            before,
        )
        if source is None:
            assert self.parent is not None, (
                f"you are required to provide a source for inputs {name} example_val {example_value} on the root tracer"
            )

        # Note [Export inputs must be explicitly passed in]
        # In eager, we are generally OK with adding graph inputs whenever we
        # want, because we take care of writing the bytecode that knows how
        # to source all the inputs.
        #
        # In export, this is bad, because you want a self-contained export
        # object which only depends on the inputs you explicitly passed to it.
        # So we are a bit more strict about what sources can become inputs
        # in export
        if self.is_export and self.parent is None:
            assert source is not None
            if not is_from_local_source(source, only_allow_input=True):
                self.output_graph.source_to_user_stacks.setdefault(source, []).append(
                    TracingContext.extract_stack()
                )

        # _used_names contains the names of all the nodes in the graph,
        # including intermediates. This ensures that we do not have a name
        # collision.
        name = get_unique_name_wrt(name, self._used_names)
        if self.input_name_to_proxy:
            prev_name = next(reversed(self.input_name_to_proxy))
            node = self.input_name_to_proxy[prev_name].node
            if before:
                ctx = self.graph.inserting_before(node)
            else:
                ctx = self.graph.inserting_after(node)
        else:
            ctx = self.graph.inserting_before(None)
        with ctx:
            proxy = self.create_proxy("placeholder", name, (), {}, type_expr=type_expr)
            set_example_value(proxy.node, example_value)
            if self.input_name_to_proxy and before:
                k, v = self.input_name_to_proxy.popitem()
                self.input_name_to_proxy[name] = proxy
                self.input_name_to_proxy[k] = v
            else:
                self.input_name_to_proxy[name] = proxy

            # For placeholder nodes, `name` is passed as a str to the target,
            # and then torch.fx decides the node.name. So, record the `target`
            # name as well in the _used_names to prevent any collision.
            self._used_names.add(name)

            # NOTE: [Auto lift basic free symbols when create_graph_input]
            # There are two sources of basic symbols:
            #
            # - They can come from inputs, e.g. when an input tensor is specified as dynamic. We handle
            # this case by intercepting at create_graph_input. Whenever we call create_graph_input, we
            # try to also lift the basic symbols in example values as graph input.
            #
            #  1. When create_graph_input for a tensor that has symbolic shapes,
            #     we look for basic symbols in its size and stride, we check if the symbol is bound
            #     in current graph (i.e. bound_symbols), if it's not bound, we'll create a placeholder
            #     for it then recursively check its parent, creates ph if not bound at parent until.
            #     reachting the top-level, where we require a source is attached to the proxy.
            #
            #  2. When create_graph_input for a tensor that contains compound exprs,
            #     for example, if an input to subgraph takes size [s1+s2//8], we'll look for the
            #     the free basic symbols in the sizes and lift all of them following 1.
            #
            #  3. When create_graph_input for a symint. The following invariants hold:
            #     a. if symint's expr is a basic symbol, we only lift it once.
            #     b. if symint's expr is compuned, we lift the expr as a single input. We won't lift The basic symbols
            #       in the compuned expr are NOT lifted. Because if the basic symbols are used inside the subgraph
            #       they will be lifted according to 3.a
            #
            # - They can come from intermediate results:
            # For example, data-dependent operators such as t.item(), t.nonzero(), where basic symbols
            # might be created. For this purpose, we track the basic symbols of intermediate results
            # immediately after they're created at wrap_fx_proxy with track_produced_symints. Notice
            # that for basic symbols that're already tracked by create_graph_input, we won't track it again.
            #
            # Also see NOTE: [Export inputs must be explicitly passed in]
            is_strict_export = self.is_export
            is_non_strict_export = torch.compiler.is_compiling()
            if not is_strict_export and not is_non_strict_export:
                if isinstance(example_value, torch.Tensor):
                    self._lift_basic_symbols(example_value, source)
                elif isinstance(example_value, (list, tuple)):
                    for i, e in enumerate(example_value):
                        if not isinstance(e, torch.Tensor):
                            continue

                        e_source = None
                        if source:
                            e_source = GetItemSource(
                                base=source,
                                index=i,
                                index_is_slice=False,
                            )

                        self._lift_basic_symbols(e, e_source)

            # Bound the symbol to ph if example_value is a SymInt with basic symbol.
            if isinstance(example_value, torch.SymInt) and isinstance(
                example_value.node.expr, sympy.Symbol
            ):
                self.bound_symbols[example_value.node.expr] = proxy
            return proxy