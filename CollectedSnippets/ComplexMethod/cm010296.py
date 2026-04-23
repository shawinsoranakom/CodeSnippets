def _strict_export(
    mod: torch.nn.Module,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None,
    preserve_module_call_signature: tuple[str, ...],
    orig_in_spec: TreeSpec,
    prefer_deferred_runtime_asserts_over_guards: bool,
    _to_aten_func: Callable,
) -> ExportArtifact:
    """
    _to_aten_func can either be `_export_to_aten_ir_make_fx` or `_export_to_aten_ir`
    """

    gm_torch_level = _export_to_torch_ir(
        # pyrefly: ignore [bad-argument-type]
        mod,
        args,
        kwargs,
        dynamic_shapes,
        preserve_module_call_signature=preserve_module_call_signature,
        restore_fqn=False,  # don't need to restore because we will do it later
        prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
        _log_export_usage=False,
    )

    # We detect the fake_mode by looking at gm_torch_level's placeholders, this is the fake_mode created in dynamo.
    (
        fake_args,
        fake_kwargs,
        dynamo_fake_mode,
    ) = _extract_fake_inputs(gm_torch_level, args, kwargs)

    fake_params_buffers = _fakify_params_buffers(dynamo_fake_mode, gm_torch_level)

    # First, we want to pass through the graph to try populating
    # val field for getattr if there is anything missing.
    # This can happen when quantization adds extra params and forgets
    # to update "val"
    for node in gm_torch_level.graph.nodes:
        if node.op == "get_attr" and "val" not in node.meta:
            attr = getattr(gm_torch_level, node.target)
            # Checks if it is not a HigherOrderOp branch or a module
            if not isinstance(attr, torch.nn.Module):
                if dynamo_fake_mode is None:
                    raise AssertionError(
                        "Cannot find dynamo_fake_mode. This could be due to the exported graph module have no placeholders."
                    )
                if is_opaque_type(type(attr)):
                    node.meta["val"] = maybe_to_fake_obj(dynamo_fake_mode, attr)
                else:
                    node.meta["val"] = dynamo_fake_mode.from_tensor(
                        attr, static_shapes=True
                    )

    # Fix the graph output signature to be tuple if scalar
    wrap_tuple = False
    # Calling gm_torch_level._out_spec is not safe because gm_torch_level might be
    # a _LazyGraphModule, which does not populate _out_spec when calling recompile().
    # TODO: Fix recompile() in  _LazyGraphModule. T207713214
    if isinstance(gm_torch_level.graph._codegen, torch.fx.graph._PyTreeCodeGen):
        out_spec = orig_out_spec = gm_torch_level.graph._codegen.pytree_info.out_spec
        orig_arg_names = gm_torch_level.graph._codegen.pytree_info.orig_args  # type: ignore[attr-defined]

        # Used to get rid of lint type error.
        if out_spec is None:
            raise AssertionError("out_spec must not be None")
        if out_spec.type not in (list, tuple):
            # aot_export expect the return type to always be a tuple.
            out_spec = pytree.treespec_tuple([out_spec])
            wrap_tuple = True
        gm_torch_level.graph._codegen.pytree_info = _PyTreeInfo(
            orig_arg_names,
            gm_torch_level._in_spec,
            out_spec,
        )
    elif isinstance(
        gm_torch_level.graph._codegen,
        torch._dynamo.functional_export._DynamoBytecodeCodeGen,
    ):
        # Since we're using bytecode codegen, we need to separately apply tuple
        # output instead of modifying pytree spec inplace.
        orig_arg_names = gm_torch_level.graph._codegen.orig_arg_names
        out_spec = orig_out_spec = None
        wrap_tuple = gm_torch_level.graph._codegen.wrap_tuple = True
    else:
        raise RuntimeError(f"Unknown codegen type: {gm_torch_level.graph._codegen}")

    gm_torch_level.recompile()

    _normalize_nn_module_stack(gm_torch_level, type(mod))

    params_buffers_to_node_meta = _collect_param_buffer_metadata(gm_torch_level)

    # When aot_export lifts the params, we lose metadata (e.g. source_fn_stack, stack_trace)
    # from the param nodes as they are treated as fresh inputs
    # Therefore, we manually extract them before calling into aot_export
    # params_buffers_to_node_meta = _collect_param_buffer_metadata(gm_torch_level)

    constant_attrs = _gather_constant_attrs(mod)
    param_buffer_table: dict[str, str] = _get_param_buffer_mapping(mod, gm_torch_level)

    # Dynamo does not track which buffers were registered as non-persistent. This info
    # is available in the original module, so we transfer it to the traced module. Also,
    # since we didn't restore original param/buffer names yet, we must use traced names.
    non_persistent_buffers = _get_non_persistent_buffers(mod)
    reverse_name_lookup = {orig: traced for traced, orig in param_buffer_table.items()}
    gm_torch_level._non_persistent_buffers_set = {
        reverse_name_lookup[name]
        for name in non_persistent_buffers
        if name in reverse_name_lookup
    }

    tx = TracingContext(dynamo_fake_mode)
    with (
        dynamo_fake_mode,
        tracing(tx),
        mock.patch.object(dynamo_fake_mode, "allow_non_fake_inputs", True),
    ):
        aten_export_artifact = _to_aten_func(
            gm_torch_level,
            # NOTE: graph module expects only positional args
            _convert_to_positional_args(orig_arg_names, fake_args, fake_kwargs),
            {},
            fake_params_buffers,
            constant_attrs,
        )

    # Decompose for readability.
    gm = aten_export_artifact.gm
    export_graph_signature = aten_export_artifact.sig
    constants = aten_export_artifact.constants

    _populate_param_buffer_metadata_to_new_gm(
        params_buffers_to_node_meta, gm, export_graph_signature
    )

    # Do some cleanups on the graph module to restore the state dict to the
    # expected form. Each of these steps should probably get fixed upstream.
    # 1. Remove tensor constants that were added as buffers.
    _rewrite_dynamo_tensor_constants(
        orig_mod_buffers=set(mod.buffers()),
        traced_mod_buffers=dict(gm_torch_level.named_buffers()),
        graph_signature=export_graph_signature,
        constants=constants,
    )
    # 2. Restore FQN of param/buffers
    _replace_param_buffer_names(param_buffer_table, export_graph_signature)

    # 3. Move non-persistent buffers to tensor constants
    _move_non_persistent_buffers_to_tensor_constants(
        mod, export_graph_signature, constants
    )

    # 4. Rewrite constants to have the same FQN as the original module.
    _remap_constants(constant_attrs, export_graph_signature, constants)

    # 5. Rename constants nodes in graph module from buffers to constants
    _rename_constants_nodes(gm, export_graph_signature)

    if orig_out_spec is None:
        out_spec = aten_export_artifact.inferred_out_spec
        if wrap_tuple:
            out_spec = out_spec.children()[0]
    else:
        out_spec = orig_out_spec
    return ExportArtifact(
        aten=aten_export_artifact,
        in_spec=orig_in_spec,
        out_spec=out_spec,
        fake_mode=dynamo_fake_mode,
        module_call_specs=gm_torch_level.meta["module_call_specs"],
    )