def _export_to_aten_ir_make_fx(
    mod: torch.nn.Module,
    fake_args,
    fake_kwargs,
    fake_params_buffers,
    constant_attrs: ConstantAttrMap,
    produce_guards_callback=None,
    transform=lambda x: x,
) -> ATenExportArtifact:
    def _make_fx_helper(stack, mod, args, kwargs, **flags):
        kwargs = kwargs or {}

        named_parameters = dict(mod.named_parameters(remove_duplicate=False))
        named_buffers = dict(mod.named_buffers(remove_duplicate=False))

        params_and_buffers = {**named_parameters, **named_buffers}
        params_and_buffers_flat, params_spec = pytree.tree_flatten(params_and_buffers)
        params_and_buffers_flat = tuple(params_and_buffers_flat)

        param_len = len(named_parameters)
        buffer_len = len(named_buffers)
        params_len = len(params_and_buffers)

        functional_call = create_functional_call(
            mod, params_spec, params_len, store_orig_mod=True
        )

        params_buffers_args: list[Any] = []
        params_buffers_args.extend(params_and_buffers_flat)
        params_buffers_args.extend(args)

        flat_fn, out_spec = create_tree_flattened_fn(
            functional_call, params_buffers_args, kwargs
        )
        flat_args, in_spec = pytree.tree_flatten((params_buffers_args, kwargs))

        @functools.wraps(flat_fn)
        def wrapped_fn(*args):
            return tuple(flat_fn(*args))

        with enable_python_dispatcher():
            ctx = nullcontext()
            non_strict_root = getattr(mod, "_export_root", None)
            if non_strict_root is not None:
                ctx = _detect_attribute_assignment(non_strict_root)  # type: ignore[assignment]

                # For any buffer that is assigned, we want to associate it to the final proxy node
                # that it is assigned to. This node can then be copied into the buffer.
                assigned_buffers: dict[str, str] = {}
                hook = register_buffer_assignment_hook(
                    non_strict_root, assigned_buffers
                )

            def custom_getattribute(self, attr, *, original_getattr, attrs_to_proxy):
                """
                The idea here is that we override subclass getattr methods to proxy
                inner tensors and metadata. Because of infinite loop shenanigans, we have
                to manually construct the getattr proxy nodes without relying on torch function
                system.
                """
                out = original_getattr(self, attr)
                if attr in attrs_to_proxy:
                    if torch._C._is_torch_function_mode_enabled():
                        if isinstance(out, torch.Tensor):
                            # When we get here there is no guarantee that we will hit the
                            # PreDispatchTorchFunctionMode, so we manually peak into the torch
                            # function mode list and tweak the PreDispatchTorchFunctionMode.
                            # This has side effect of proxying stuff like
                            # proxy.node.meta["val"] = extract_val(val) because at that time, torch function
                            # mode is still active. It seems bad to turn it off inside proxy_tensor.py, so
                            # I guess we will just rely on DCE for now to remove extra stuff like detach
                            torch_function_mode_stack = (
                                torch.overrides._get_current_function_mode_stack()
                            )
                            for mode in torch_function_mode_stack:
                                if isinstance(mode, PreDispatchTorchFunctionMode):
                                    tracer = mode.tracer
                                    proxy = get_proxy_slot(self, tracer).proxy
                                    inner_proxy = tracer.create_proxy(
                                        "call_function",
                                        torch.ops.export.access_subclass_inner_tensor.default,
                                        (proxy, attr),
                                        {},
                                    )
                                    track_tensor_tree(
                                        out, inner_proxy, constant=None, tracer=tracer
                                    )
                return out

            @contextmanager
            def override_getattribute_for_subclasses(args):
                """
                Context manager that temporarily monkey patches
                tensor.__getattribute__ so that we can intercept it at
                torch_function layer.
                """

                # Dictionary that tracks subclass type to original getattr function
                # and the attributes we can proxy.
                tensor_type_to_old_getattribute: dict[
                    type[torch.Tensor], tuple[Callable, set[str]]
                ] = {}
                for arg in args:
                    subclass_types_to_instances: dict[
                        type[torch.Tensor], list[type[torch.Tensor]]
                    ] = get_subclass_typing_container(arg)
                    for subclass_type in subclass_types_to_instances:
                        if subclass_type not in tensor_type_to_old_getattribute:
                            if len(subclass_types_to_instances[subclass_type]) == 0:
                                raise AssertionError(
                                    f"subclass_types_to_instances[{subclass_type}] must not be empty"
                                )
                            instance = subclass_types_to_instances[subclass_type][0]
                            # Query subclass specific attrs
                            attrs_to_proxy = set(dir(instance)) - set(dir(torch.Tensor))
                            tensor_type_to_old_getattribute[subclass_type] = (
                                subclass_type.__getattribute__,  # type: ignore[attr-defined]
                                attrs_to_proxy,
                            )

                try:
                    for k, (
                        old_getattr,
                        attrs_to_proxy,
                    ) in tensor_type_to_old_getattribute.items():
                        custom = functools.partialmethod(
                            custom_getattribute,
                            original_getattr=old_getattr,
                            attrs_to_proxy=attrs_to_proxy,
                        )
                        k.__getattribute__ = custom  # type: ignore[assignment, attr-defined]
                    yield
                finally:
                    for k, (old_getattr, _) in tensor_type_to_old_getattribute.items():
                        k.__getattribute__ = old_getattr  # type: ignore[method-assign, attr-defined]

            @contextmanager
            def _maybe_restore_grad_state():
                """
                When pre-dispatch export accidentally change grad state, we restore it back.
                This can happen when we are calling torch._C._set_grad_enabled directly in the
                forward.
                """
                old_state = torch.is_grad_enabled()
                try:
                    yield
                finally:
                    torch._C._set_grad_enabled(old_state)

            with (
                ctx,
                override_getattribute_for_subclasses(flat_args),
                _maybe_restore_grad_state(),
            ):
                gm = make_fx(
                    wrapped_fn,
                    record_module_stack=True,
                    pre_dispatch=True,
                )(*flat_args)

            if non_strict_root is not None:
                input_names = _graph_input_names(gm)
                buffer_input_names = {
                    name: input_names[param_len + i]
                    for i, (name, buf) in enumerate(non_strict_root._buffers.items())
                    if buf is not None
                }
                output_node = list(gm.graph.nodes)[-1]
                # We copy nodes corresponding to buffer assignments to buffers in the graph.
                for buf, name in assigned_buffers.items():  # type: ignore[possibly-undefined]
                    buf_node = _find_node(gm, buffer_input_names[buf])
                    name_node = _find_node(gm, name)
                    with gm.graph.inserting_before(output_node):
                        new_node = gm.graph.create_node(
                            "call_function",
                            torch.ops.aten.copy_.default,
                            args=(buf_node, name_node),
                        )
                        new_node.meta = name_node.meta

                hook.remove()  # type: ignore[possibly-undefined]

            def _is_impure(node):
                if node.op == "call_function" and node.target in (
                    # In export, we ignore any op that is related to
                    # eager mode profiling call. The expectation is
                    # that either runtimes provide their own profiling
                    # OR user wrap the compiled region on a profiling in
                    # later stage.
                    torch.ops.profiler._record_function_enter.default,
                    torch.ops.profiler._record_function_enter_new.default,
                    torch.ops.profiler._record_function_exit._RecordFunction,
                    # In theory, we could fix this dead detach and getattr nodes
                    # from subclass tensors if we carefully rewrite track_tensor_tree
                    # in a way that it doesn't do any tensor methods.
                    torch.ops.aten.detach.default,
                    torch.ops.export.access_subclass_inner_tensor.default,
                ):
                    return False
                return True

            gm.graph.eliminate_dead_code(_is_impure)

        # create graph signature
        if out_spec.spec is None:
            raise AssertionError("out_spec.spec is None!")
        input_names = _graph_input_names(gm)
        output_names = _graph_output_names(gm)
        sig = GraphSignature(
            parameters=list(named_parameters),
            buffers=list(named_buffers),
            # pyrefly: ignore[bad-argument-type]
            user_inputs=input_names[params_len:],
            user_outputs=output_names,
            # pyrefly: ignore[no-matching-overload]
            inputs_to_parameters=dict(zip(input_names[0:param_len], named_parameters)),
            # pyrefly: ignore[no-matching-overload]
            inputs_to_buffers=dict(
                zip(input_names[param_len : param_len + buffer_len], named_buffers)
            ),
            buffers_to_mutate={},
            parameters_to_mutate={},
            user_inputs_to_mutate={},
            in_spec=in_spec,
            out_spec=out_spec.spec,
            backward_signature=None,
            input_tokens=[],
            output_tokens=[],
        )
        return gm, sig

    # This _reparameterize_module makes sure inputs and module.params/buffers have the same fake_mode,
    # otherwise aot_export_module will error out because it sees a mix of fake_modes.
    # And we want aot_export_module to use the fake_tensor mode in dynamo to keep the pipeline easy to reason about.
    with ExitStack() as stack:
        stack.enter_context(
            torch.nn.utils.stateless._reparametrize_module(
                mod,
                fake_params_buffers,
                tie_weights=True,
                strict=True,
                stack_weights=True,
            )
        )
        stack.enter_context(_ignore_backend_decomps())
        stack.enter_context(_compiling_state_context())
        gm, graph_signature = transform(_make_fx_helper)(
            stack,
            mod,
            fake_args,
            trace_joint=False,
            kwargs=fake_kwargs,
        )

        # [NOTE] In training IR, we don't run
        # any DCE as a result we preserve constant
        # nodes in the graph. make_fx invariant is that
        # they don't guarantee every node gets a meta['val']
        # field. Since the actual value is already hardcoded in
        # graph, the node.meta here actually doesn't matter. But
        # we do this to make spec verifier happy.
        for node in gm.graph.nodes:
            if (
                node.op == "call_function"
                and len(node.users) == 0
                and "val" not in node.meta
            ):
                node.meta["val"] = None

        if isinstance(mod, torch.fx.GraphModule) and hasattr(mod, "meta"):
            gm.meta.update(mod.meta)

    # See comment in _export_to_aten_ir()
    if produce_guards_callback:
        try:
            produce_guards_callback(gm)
        except (ConstraintViolationError, ValueRangeError) as e:
            raise UserError(UserErrorType.CONSTRAINT_VIOLATION, str(e))  # noqa: B904

    return _produce_aten_artifact(
        gm=gm,
        mod=mod,
        constant_attrs=constant_attrs,
        graph_signature=graph_signature,
        pre_dispatch=True,
        fake_args=fake_args,
        fake_kwargs=fake_kwargs,
        fake_params_buffers=fake_params_buffers,
    )