def begin_capture(
        self,
        inputs: list[torch.Tensor],
        sizes: list[int],
        scalars: list[IntLikeType | FloatLikeType],
        origins: list[list[tuple[int, str]]],
        accumulate_grad: bool,
        check_nans: bool,
    ) -> tuple[str, list[torch.Tensor], list[IntLikeType], list[FloatLikeType]]:
        counters["compiled_autograd"]["captures"] += 1
        self.id = next(COMPILE_COUNTER)
        self.aot_id_counter: dict[int, int] = defaultdict(int)
        self.compile_context = make_compile_context(self.id)
        self.compile_context.__enter__()
        self.nan_checker = NaNChecker(accumulate_grad) if check_nans else None
        self.start_time_ns = time.time_ns()
        get_chromium_event_logger().log_event_start(
            "compiled_autograd",
            self.start_time_ns,
            {"graph_id": self.id},
            log_pt2_compile_event=True,
        )
        self.fx_tracer.root = torch.nn.Module()
        self.fx_tracer.graph = torch.fx.Graph(tracer_cls=PythonKeyTracer)
        self.fx_tracer.tensor_attrs = {}
        self.symnode_proxy_lookup = {}
        (
            args_proxy,
            self.sizes_proxy,
            self.scalars_proxy,
            self.hooks_proxy,
            self.packed_data_proxy,
        ) = (
            self.fx_tracer.create_proxy("placeholder", name, (), {})
            for name in _graph_placeholders
        )

        self.stack.enter_context(preserve_node_meta())
        inputs_origins, sizes_origins, scalars_origins = origins

        # Turn on PythonDispatcher during initial trace to make it identifiable
        # that tracing is happening, which is needed to prevent hashing symints
        self.stack.enter_context(enable_python_dispatcher())

        # tensor inputs to fake tensors
        x = inputs[0]  # mypy will complain about unbound x
        try:
            for idx, x in enumerate(inputs):
                inputs[idx] = self.wrap_fake(x, self.source("inputs", idx))
        except Exception as e:
            raise NotImplementedError(
                f"Found tensor of type {type(x)}, which is not supported by FakeTensorMode. {TURN_OFF_MSG}"
            ) from e
        self.bind_objects_to_proxies(inputs, args_proxy, inputs_origins)

        # size inputs to symints
        sym_sizes = [
            self.shape_env.create_unspecified_symint_and_symbol(
                val,
                self.source("sizes", idx),
                DimDynamic.DYNAMIC,
            )
            for idx, val in enumerate(sizes)
        ]

        # We want to mark every size as dynamic, but since there's no way to
        # mark a primitive `int` as dynamic, we need to wrap it in a tensor.
        # In the graph, we unwrap it with `unwrap_maybe_dynamic_int` back into a primitive.
        proxies = [self.sizes_proxy[i] for i in range(len(sym_sizes))]  # type: ignore[index]
        for i, symint in enumerate(sym_sizes):
            proxies[i] = self.fx_tracer.create_proxy(
                "call_function",
                unwrap_maybe_dynamic_int,
                (proxies[i],),
                {},
            )
            if not isinstance(symint, int):
                self.symnode_proxy_lookup[symint.node] = proxies[i]
        proxies = self.bind_objects_to_proxies(sym_sizes, proxies, sizes_origins)

        for idx, val in enumerate(scalars):
            source = self.source("scalars", idx)
            if isinstance(val, int):
                scalars[idx] = self.shape_env.create_unspecified_symint_and_symbol(
                    val,
                    source,
                    DimDynamic.DYNAMIC,
                )
            elif isinstance(val, float):
                scalars[idx] = self.shape_env.create_symfloatnode(
                    self.shape_env.create_unspecified_symbol(
                        val,
                        source=source,
                        dynamic_dim=DimDynamic.DYNAMIC,
                    ),
                    hint=val,
                    source=source,
                )
            else:
                raise AssertionError("Unexpected scalar type: ", type(val))
        self.bind_objects_to_proxies(scalars, self.scalars_proxy, scalars_origins)
        for i, symval in enumerate(scalars):
            self.symnode_proxy_lookup[symval.node] = self.scalars_proxy[i]  # type: ignore[union-attr]

        # TODO(jansel): are all these modes needed?
        self.stack.enter_context(decompose({}))
        self.stack.enter_context(self.fake_tensor_mode)
        self.stack.enter_context(self.proxy_mode)
        self.stack.enter_context(disable_autocast_cache())
        # Needed to make sure we don't accidentally specialize any symbols
        assert self.fake_tensor_mode.shape_env is not None
        env = self.fake_tensor_mode.shape_env
        self.stack.enter_context(
            torch.fx.experimental.symbolic_shapes._suppress_guards(env)
        )
        # pyrefly: ignore [bad-return]
        return (
            str(CompileContext.current_compile_id()),
            inputs,
            sym_sizes,
            scalars,  # type: ignore[return-value]
        )