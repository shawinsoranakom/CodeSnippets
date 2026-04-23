def track_produced_symints(
        self, example_value: Any, e_proxy: LazyProxy | torch.fx.Proxy
    ) -> None:
        # When binding the symbols in an example_value, we bind the symbols
        # to the proxy's associated Tracer instead of current tracer.
        # This is because:
        # 1. We may be calling wrap_tensors during speculate_subgraph because
        # the variables are lazily realized. The proxy are top-level phs but
        # current tracer is a subtracer.
        # 2. For autograd.Function, we trace the backward graph with a new tracer
        # whose parent is the forward tracer, but we're using all the proxies created
        # in forward tracer to trace the backward.
        # For example, forward calls save_for_backward for a input tensor t.
        # Backward calls t.tolist(). In this case, all the proxies that backward tracer
        # sees are from parent tracer (i.e. the forward tracer). (e.g. t[0].item())
        # See test_validate_outputs_unbacked for repro on 2.
        tracer = e_proxy.tracer
        assert isinstance(tracer, SubgraphTracer)

        def need_bind(s: Any) -> bool:
            from torch.fx.experimental.symbolic_shapes import is_symbolic

            return (
                is_symbolic(s)
                and isinstance(s.node.expr, sympy.Symbol)
                and s.node.expr not in self.bound_symbols
            )

        def _proxy_with_example_value(
            example_value: Any, *args: Any, **kwargs: Any
        ) -> fx.Proxy:
            # We need to insert proxy for creating sym_size/sym_stride/sym_storage right after e_proxy
            nonlocal e_proxy
            e_proxy = e_proxy() if isinstance(e_proxy, LazyProxy) else e_proxy
            assert isinstance(e_proxy, torch.fx.Proxy)
            with tracer.graph.inserting_after(e_proxy.node):
                proxy = tracer.create_proxy(*args, **kwargs)
                set_example_value(proxy.node, example_value)
                return proxy

        if isinstance(example_value, torch.Tensor):
            for i, s in enumerate(example_value.size()):
                if need_bind(s):
                    log.debug(
                        "track_produced_symints %s for %s.size()[%s] at debug_level %s",
                        s,
                        e_proxy,
                        i,
                        tracer.debug_level,
                    )
                    lazy_proxy = LazyProxy(
                        tracer,
                        _proxy_with_example_value,
                        s,
                        "call_function",
                        torch.ops.aten.sym_size.int,
                        (e_proxy, i),
                        {},
                        type_expr=type(s),
                    )
                    self.track_produced_symints(s, lazy_proxy)

            storage_offset = example_value.storage_offset()
            if need_bind(storage_offset):
                log.debug(
                    "track_produced_symints %s for %s.storage_offset() at debug_level %s",
                    storage_offset,
                    e_proxy,
                    tracer.debug_level,
                )
                lazy_proxy = LazyProxy(
                    tracer,
                    _proxy_with_example_value,
                    storage_offset,
                    "call_function",
                    torch.ops.aten.sym_storage_offset,
                    (e_proxy,),
                    {},
                    type_expr=type(storage_offset),
                )
                self.track_produced_symints(storage_offset, lazy_proxy)

            if example_value.layout is torch.strided:
                for i, s in enumerate(example_value.stride()):
                    if need_bind(s):
                        log.debug(
                            "track_produced_symints %s for %s.stride()[%s] at debug_level %s",
                            s,
                            e_proxy,
                            i,
                            tracer.debug_level,
                        )
                        lazy_proxy = LazyProxy(
                            tracer,
                            _proxy_with_example_value,
                            s,
                            "call_function",
                            torch.ops.aten.sym_stride.int,
                            (e_proxy, i),
                            {},
                            type_expr=type(s),
                        )
                        self.track_produced_symints(s, lazy_proxy)

            elif example_value.layout is torch.sparse_coo:
                self.track_produced_symints(example_value._indices(), e_proxy)
                self.track_produced_symints(example_value._values(), e_proxy)
            elif example_value.layout in {torch.sparse_csr, torch.sparse_bsr}:
                self.track_produced_symints(example_value.crow_indices(), e_proxy)
                self.track_produced_symints(example_value.col_indices(), e_proxy)
            elif example_value.layout in {torch.sparse_csc, torch.sparse_bsc}:
                self.track_produced_symints(example_value.ccol_indices(), e_proxy)
                self.track_produced_symints(example_value.row_indices(), e_proxy)
            if is_traceable_wrapper_subclass(example_value):
                attrs, ctx = example_value.__tensor_flatten__()
                for attr in attrs:
                    inner_t = getattr(example_value, attr)
                    self.track_produced_symints(inner_t, getattr(e_proxy, attr))
        elif isinstance(example_value, torch.SymInt):
            if need_bind(example_value):
                expr = example_value.node.expr
                tracer.bound_symbols[expr] = e_proxy