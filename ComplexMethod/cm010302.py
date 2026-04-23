def _decompose_and_get_gm_with_new_signature_constants(
    ep: "ExportedProgram",
    *,
    cia_to_decomp: dict[torch._ops.OperatorBase, Callable],
    python_decomp_table: dict[torch._ops.OperatorBase, Callable],
    joint_loss_index: int | None,
    decompose_custom_triton_ops,
):
    from torch._export.passes.lift_constants_pass import _materialize_and_lift_constants
    from torch._functorch.aot_autograd import aot_export_module
    from torch.export._trace import (
        _disable_custom_triton_op_functional_decomposition,
        _export_to_aten_ir,
        _ignore_backend_decomps,
        _verify_nn_module_stack,
        _verify_placeholder_names,
        _verify_stack_trace,
    )
    from torch.fx.experimental.symbolic_shapes import ShapeEnv

    def _is_joint_ir_decomp(ep, joint_loss_index):
        return (
            joint_loss_index is not None
            or ep.graph_signature.backward_signature is not None
        )

    if not _is_joint_ir_decomp(ep, joint_loss_index):
        mod = ep.module()

        wrapped_params_buffers = {
            **dict(mod.named_parameters(remove_duplicate=False)),
            **dict(mod.named_buffers(remove_duplicate=False)),
        }

        from torch._functorch._aot_autograd.subclass_parametrization import (
            unwrap_tensor_subclass_parameters,
        )

        # [NOTE] Unwrapping subclasses AOT
        # In torch.compile, the subclass unwrapping/wrapping happen at runtime
        # but at export, this is impossible as it is intended to be run on
        # C++ environment. As a result, we unwrap subclass parameters AOT. After this,
        # ExportedProgram state_dict won't be same as eager model because eager model
        # could have subclass weights while ExportedProgram will have desugared versions.
        # This is fine because run_decompositions is supposed to specialize to post-autograd
        # graph where the subclass desugaring is supposed to happen.
        unwrap_tensor_subclass_parameters(mod)
        unwrapped_params_buffers = {
            **dict(mod.named_parameters(remove_duplicate=False)),
            **dict(mod.named_buffers(remove_duplicate=False)),
        }

        # TODO T204030333
        fake_mode = _detect_fake_mode_from_gm(ep.graph_module)
        if fake_mode is None:
            fake_mode = FakeTensorMode(shape_env=ShapeEnv(), export=True)

        # Fix the graph output signature to be tuple if scalar
        out_spec = mod._out_spec

        if not isinstance(mod.graph._codegen, _PyTreeCodeGen):
            raise AssertionError(
                f"expected mod.graph._codegen to be _PyTreeCodeGen, got {type(mod.graph._codegen)}"
            )
        orig_arg_names = mod.graph._codegen.pytree_info.orig_args

        # aot_export expect the return type to always be a tuple.
        if out_spec is None:
            raise AssertionError("out_spec must not be None")
        if out_spec.type not in (list, tuple):
            out_spec = pytree.treespec_tuple([out_spec])

        mod.graph._codegen = _PyTreeCodeGen(
            _PyTreeInfo(
                orig_arg_names,
                mod._in_spec,
                out_spec,
            )
        )

        mod.recompile()

        # the exported module will store constants & non-persistent buffers such that
        # retracing treats them as persistent buffers, so we inform the constants lifting pass
        # and overwrite the new graph signature using the previous program.
        _collect_and_set_constant_attrs(ep.graph_signature, ep.constants, mod)

        # When we have a module with constant attributes, AotDispatcher doesn't actually
        # wrap them as functional tensors, because dynamo would have already made it buffer.
        # In non-strict case, however, AotDispatcher can intercept constants, causing it to not
        # functionalize the operators that are operating on constant tensors. Since dynamo already
        # wraps constants as buffers, we temporarily register the constants as buffers and undo this
        # operation after AOTDispatcher is done.
        temp_registered_constants = _register_constants_as_buffers(
            mod, ep.state_dict, ep.graph_signature.non_persistent_buffers
        )

        # get params & buffers after excluding constants
        fake_params_buffers = _fakify_params_buffers(fake_mode, mod)

        params_buffers_to_node_meta = _collect_param_buffer_metadata(mod)

        # TODO (tmanlaibaatar) Ideally run_decomp should just call _non_strict_export
        # but due to special handling of constants as non-persistent buffers make it little
        # difficult. But we should unify this code path together. T206837815
        from torch._export.non_strict_utils import (
            _enable_graph_inputs_of_type_nn_module,
            _fakify_script_objects,
        )

        retracing_args = []
        for node in mod.graph.nodes:
            if node.op == "placeholder":
                if isinstance(node.meta["val"], CustomObjArgument):
                    real_script_obj = None
                    if node.meta["val"].fake_val is None:
                        real_script_obj = ep.constants[node.meta["val"].name]
                    else:
                        real_script_obj = node.meta["val"].fake_val.real_obj
                    retracing_args.append(real_script_obj)
                else:
                    retracing_args.append(node.meta["val"])

        tx = TracingContext(fake_mode)

        with (
            fake_mode,
            _override_composite_implicit_decomp(
                cia_to_decomp,
            ),
            _enable_graph_inputs_of_type_nn_module(ep.example_inputs),
            tracing(tx),
        ):
            retracing_args_unwrapped = pytree.tree_unflatten(
                retracing_args, mod._in_spec
            )
            # this requires empty kwargs, but not in pytree.flattened format
            with _fakify_script_objects(
                mod,
                (
                    *retracing_args_unwrapped[0],
                    *retracing_args_unwrapped[1].values(),
                ),
                {},
                fake_mode,
            ) as (
                patched_mod,
                new_fake_args,
                new_fake_kwargs,
                new_fake_constant_attrs,
                map_fake_to_real,
            ):
                aten_export_artifact = _export_to_aten_ir(
                    patched_mod,
                    new_fake_args,
                    new_fake_kwargs,
                    fake_params_buffers,
                    new_fake_constant_attrs,
                    decomp_table=python_decomp_table,
                    _prettify_placeholder_names=False,
                    decompose_custom_triton_ops=decompose_custom_triton_ops,
                )

                # aten_export_artifact.constants contains only fake script objects, we need to map them back
                aten_export_artifact.constants = {
                    fqn: (
                        map_fake_to_real[obj]
                        if isinstance(obj, FakeScriptObject)
                        else obj
                    )
                    for fqn, obj in aten_export_artifact.constants.items()
                }

                gm = aten_export_artifact.gm
                new_graph_signature = aten_export_artifact.sig

                # In the previous step, we assume constants as buffers for AOTDispatcher to
                # functianalize properly, so undo that here
                new_graph_signature = (
                    _override_graph_signature_for_temp_registered_constants(
                        new_graph_signature, temp_registered_constants
                    )
                )

                _populate_param_buffer_metadata_to_new_gm(
                    params_buffers_to_node_meta, gm, new_graph_signature
                )

                # overwrite signature for non-persistent buffers
                new_graph_signature = _overwrite_signature_for_non_persistent_buffers(
                    ep.graph_signature, new_graph_signature
                )

                constants = _materialize_and_lift_constants(
                    gm, new_graph_signature, new_fake_constant_attrs
                )

                placeholder_naming_pass(
                    gm,
                    new_graph_signature,
                    patched_mod,
                    new_fake_args,
                    new_fake_kwargs,
                    fake_params_buffers,
                    constants,
                )

        _verify_nn_module_stack(gm)
        _verify_stack_trace(gm)
        _verify_placeholder_names(gm, new_graph_signature)

        gm, new_graph_signature = _remove_unnecessary_copy_op_pass(
            gm, new_graph_signature
        )

        # When we apply parameterization rule to unwrap
        # subclasses, the state dict will now have different
        # desugared parameters. We need to manually filter those
        # and update the ep.state_dict. Ideally, we should just return
        # the state dict of ep.module but ep.module only stores params
        # buffers that participate in forward. If we undo this behavior,
        # it would break some downstream users.
        new_state_dict = {
            **ep.state_dict,
            **{
                name: p
                for name, p in unwrapped_params_buffers.items()
                if name not in wrapped_params_buffers
            },
        }

        for name, p in wrapped_params_buffers.items():
            # Buffers can be persistent/non-persistent
            if name not in new_state_dict:
                if isinstance(p, torch.nn.Parameter):
                    raise AssertionError(
                        f"expected {name!r} not to be a torch.nn.Parameter when not in state_dict"
                    )

            if name in new_state_dict:
                if name not in unwrapped_params_buffers:
                    new_state_dict.pop(name)

        return gm, new_graph_signature, new_state_dict

    old_placeholders = [
        node for node in ep.graph_module.graph.nodes if node.op == "placeholder"
    ]
    fake_args = [node.meta["val"] for node in old_placeholders]

    buffers_to_remove = [name for name, _ in ep.graph_module.named_buffers()]
    for name in buffers_to_remove:
        delattr(ep.graph_module, name)

    # TODO(zhxhchen17) Return the new graph_signature directly.
    fake_mode_det = detect_fake_mode(fake_args)
    fake_mode_ctx = contextlib.nullcontext() if fake_mode_det is None else fake_mode_det  # type: ignore[assignment]
    custom_triton_ops_decomposition_ctx = (
        contextlib.nullcontext
        if decompose_custom_triton_ops
        else _disable_custom_triton_op_functional_decomposition
    )
    with (
        _ignore_backend_decomps(),
        fake_mode_ctx,
        _override_composite_implicit_decomp(cia_to_decomp),
        custom_triton_ops_decomposition_ctx(),
    ):
        gm, graph_signature = aot_export_module(
            ep.graph_module,
            fake_args,
            # pyrefly: ignore[bad-argument-type]
            decompositions=python_decomp_table,
            trace_joint=joint_loss_index is not None,
            output_loss_index=(
                joint_loss_index if joint_loss_index is not None else None
            ),
        )
        assert isinstance(gm, torch.fx.GraphModule)  # noqa: S101
        gm.graph.eliminate_dead_code()

    # Update the signatures with the new placeholder names in case they
    # changed when calling aot_export
    def update_arg(old_arg, new_ph):
        if isinstance(old_arg, ConstantArgument):
            return old_arg
        elif isinstance(old_arg, TensorArgument):
            return TensorArgument(name=new_ph.name)
        elif isinstance(old_arg, SymIntArgument):
            return SymIntArgument(name=new_ph.name)
        elif isinstance(old_arg, SymFloatArgument):
            return SymFloatArgument(name=new_ph.name)
        elif isinstance(old_arg, SymBoolArgument):
            return SymBoolArgument(name=new_ph.name)
        raise RuntimeError(f"Type of old_arg not supported: {type(old_arg)}")

    new_placeholders = [node for node in gm.graph.nodes if node.op == "placeholder"]
    new_outputs: tuple[torch.fx.Node, ...] = tuple(gm.graph.output_node().args[0])  # type: ignore[arg-type]

    # rename the placeholders
    if len(new_placeholders) != len(old_placeholders):
        raise AssertionError(
            f"new_placeholders length {len(new_placeholders)} does not match old_placeholders length {len(old_placeholders)}"
        )
    for old_ph, new_ph in zip(old_placeholders, new_placeholders):
        new_ph.name = new_ph.target = old_ph.name

    # handle name collisions with newly decomposed graph nodes
    name_map = {}
    find_available: dict[str, int] = defaultdict(int)
    used_names: set[str] = set()
    for ph in new_placeholders:
        name_map[ph.name] = ph.name
        _build_cache(ph.name, find_available, used_names)
    for node in gm.graph.nodes:
        if node.op == "placeholder":
            continue
        node.name = _rename_without_collisions(
            name_map, find_available, used_names, node.name, node.name
        )

    # propagate names to higher order op subgraphs
    _name_hoo_subgraph_placeholders(gm)

    # Run this pass before creating input/output specs, since size-related CSE/DCE might affect output signature.
    # Overwrite output specs afterwards.
    from torch._export.passes._node_metadata_hook import (
        _node_metadata_hook,
        _set_node_metadata_hook,
    )
    from torch._functorch._aot_autograd.input_output_analysis import _graph_output_names

    if not torch._dynamo.config.do_not_emit_runtime_asserts:
        stack_trace = (
            'File "torch/fx/passes/runtime_assert.py", line 24, '
            "in insert_deferred_runtime_asserts"
        )
        shape_env = _get_shape_env(gm)
        if shape_env is not None:
            with _set_node_metadata_hook(
                gm,
                functools.partial(
                    _node_metadata_hook, metadata={"stack_trace": stack_trace}
                ),
            ):
                insert_deferred_runtime_asserts(
                    gm,
                    shape_env,
                    f"exported program: {first_call_function_nn_module_stack(gm.graph)}",
                    export=True,
                )

    # update output specs
    gm.recompile()
    for output, name in zip(new_outputs, _graph_output_names(gm)):
        if name is not None:
            output.name = name

    # To match the output target with correct input for input mutations
    # need to find the old to new placeholder map
    old_new_placeholder_map = {
        spec.arg.name: new_placeholders[i].name
        for i, spec in enumerate(ep.graph_signature.input_specs)
        if not isinstance(spec.arg, ConstantArgument)
    }

    input_specs = [
        InputSpec(
            spec.kind,
            update_arg(spec.arg, new_placeholders[i]),
            spec.target,
            spec.persistent,
        )
        for i, spec in enumerate(ep.graph_signature.input_specs)
    ]

    output_specs = []

    # handle buffer & input mutations; these appear before loss output & gradients
    # (1) ep.graph_signature.input_specs tells us types of inputs
    # (2) graph_signature.user_inputs tells us node input names in order
    # (3) graph_signature.user_inputs_to_mutate tells us buffer & input mutations
    # map (3) -> (2) for input order, -> (1) for input type
    user_inputs_index = {name: i for i, name in enumerate(graph_signature.user_inputs)}
    mutation_names = list(graph_signature.user_inputs_to_mutate.keys())
    expected_names = [node.name for node in new_outputs[: len(mutation_names)]]
    if mutation_names != expected_names:
        raise AssertionError(
            f"mutation_names {mutation_names} does not match expected {expected_names}"
        )
    for output_name, input_name in graph_signature.user_inputs_to_mutate.items():
        i = user_inputs_index[input_name]
        input_spec = ep.graph_signature.input_specs[i]
        if input_spec.kind not in (InputKind.USER_INPUT, InputKind.BUFFER):
            raise AssertionError(
                f"expected input_spec.kind to be USER_INPUT or BUFFER, got {input_spec.kind}"
            )
        output_kind = (
            OutputKind.BUFFER_MUTATION
            if input_spec.kind == InputKind.BUFFER
            else OutputKind.USER_INPUT_MUTATION
        )
        target = (
            input_spec.target
            if input_spec.kind == InputKind.BUFFER
            else input_spec.arg.name
        )
        output_specs.append(
            OutputSpec(
                kind=output_kind,
                arg=TensorArgument(name=output_name),
                target=target,
            )
        )

    # handle actual user outputs
    for i, spec in enumerate(ep.graph_signature.output_specs):
        output_specs.append(
            OutputSpec(
                OutputKind.LOSS_OUTPUT if i == joint_loss_index else spec.kind,
                update_arg(spec.arg, new_outputs[len(mutation_names) + i]),
                old_new_placeholder_map.get(spec.target, spec.target),
            )
        )

    if joint_loss_index is not None:
        if graph_signature.backward_signature is None:
            raise AssertionError(
                "graph_signature.backward_signature must not be None when joint_loss_index is set"
            )
        gradients = graph_signature.backward_signature.gradients_to_user_inputs
        if len(graph_signature.user_inputs) != len(ep.graph_signature.input_specs):
            raise AssertionError(
                f"graph_signature.user_inputs length {len(graph_signature.user_inputs)} does not match "
                f"input_specs length {len(ep.graph_signature.input_specs)}"
            )
        specs = {
            graph_signature.user_inputs[i]: spec
            for i, spec in enumerate(ep.graph_signature.input_specs)
            if isinstance(spec.arg, TensorArgument)
        }
        for node in new_outputs[len(output_specs) :]:
            source = gradients[node.name]
            spec = specs[source]  # type: ignore[index]
            if spec.kind == InputKind.PARAMETER:
                kind = OutputKind.GRADIENT_TO_PARAMETER
                target = spec.target
            elif spec.kind == InputKind.USER_INPUT:
                kind = OutputKind.GRADIENT_TO_USER_INPUT
                target = source
            else:
                raise AssertionError(f"Unknown input kind: {spec.kind}")
            output_specs.append(
                OutputSpec(
                    kind,
                    TensorArgument(name=node.name),
                    target,
                )
            )

    if len(new_placeholders) != len(old_placeholders):
        raise AssertionError(
            f"new_placeholders length {len(new_placeholders)} does not match old_placeholders length {len(old_placeholders)}"
        )

    new_graph_signature = ExportGraphSignature(
        input_specs=input_specs, output_specs=output_specs
    )
    # NOTE: aot_export adds symint metadata for placeholders with int
    # values; since these become specialized, we replace such metadata with
    # the original values.
    # Also, set the param/buffer metadata back to the placeholders.
    for old_node, new_node in zip(old_placeholders, new_placeholders):
        if not isinstance(old_node.meta["val"], torch.Tensor):
            new_node.meta["val"] = old_node.meta["val"]

        if (
            new_node.target in new_graph_signature.inputs_to_parameters
            or new_node.target in new_graph_signature.inputs_to_buffers
        ):
            for k, v in old_node.meta.items():
                new_node.meta[k] = v
    return gm, new_graph_signature, ep.state_dict