def aot_dispatch_base_graph(
    flat_fn: TraceFn,
    flat_args: list[FxValue],
    flat_args_descs: list[AOTInput],
    aot_config: AOTConfig,
    *,
    fw_metadata: ViewAndMutationMeta,
) -> tuple[torch.fx.GraphModule, list[FxValue], list[AOTInput], SubclassMeta | None]:
    # aot_dispatch_base requires functionalization, but doesn't need to handle as many cases as the autograd case.
    # The cases that aot_dispatch_base doesn't need to handle include:
    # - outputs that are aliases of graph intermediates
    # - outputs that are aliases of graph inputs
    # While cases that it does need to handle include:
    # - input mutations (including when inputs are aliases of each other)
    # - input metadata mutations
    fn_to_trace = fn_input_mutations_to_outputs(
        flat_fn,
        flat_args_descs,
        fw_metadata,
        keep_data_input_mutations=aot_config.keep_inference_input_mutations,
    )
    # TODO: replace with AOTDispatchSubclassWrapper once we refactor
    # fn_input_mutations_to_outputs and create_functionalized_fn
    # into CompilerWrappers.
    tracing_state = _prepare_graph_capture_tracing(
        fn_to_trace,
        flat_args,
        flat_args_descs,
        flat_fn,
        fw_metadata=fw_metadata,
        aot_config=aot_config,
        trace_joint=False,
    )
    fn_to_trace = tracing_state.fn_to_trace
    updated_flat_args_subclasses_desugared = tracing_state.flat_args
    updated_flat_args_subclasses_desugared_descs = tracing_state.flat_args_descs
    maybe_subclass_meta = tracing_state.maybe_subclass_meta

    aot_graphs_log.debug(
        "aot_config id: %s, fw_metadata=%s,subclass_metadata=%s",
        aot_config.aot_id,
        fw_metadata,
        maybe_subclass_meta,
    )

    # We track buffer assignments when exporting in non-strict mode.
    # (In contrast, strict mode errors on any attribute assignment.)
    mod_when_exporting_non_strict = root_module_when_exporting_non_strict(flat_fn)
    if aot_config.is_export and mod_when_exporting_non_strict is not None:
        # For any buffer that is assigned, we want to associate it to the final proxy node
        # that it is assigned to. This node can then be added as a buffer mutation output.
        assigned_buffers: dict[str, str] = {}
        hook = register_buffer_assignment_hook(
            mod_when_exporting_non_strict, assigned_buffers
        )

    (
        fw_module,
        saved_updated_flat_args_subclasses_desugared,
    ) = _create_graph_and_save_traced_inputs(
        fn_to_trace,
        updated_flat_args_subclasses_desugared,
        updated_flat_args_subclasses_desugared_descs,
        aot_config=aot_config,
    )
    saved_updated_flat_args_subclasses_desugared_descs = (
        updated_flat_args_subclasses_desugared_descs
    )

    if aot_config.is_export and mod_when_exporting_non_strict is not None:
        # We update metadata to consider any assigned buffers as buffer mutations.
        i = len(dict(mod_when_exporting_non_strict.named_parameters()))
        for name, _ in mod_when_exporting_non_strict.named_buffers():
            if name in assigned_buffers and not fw_metadata.input_info[i].mutates_data:  # type: ignore[possibly-undefined]
                fw_metadata.input_info[i] = dataclasses.replace(
                    fw_metadata.input_info[i], mutates_data=True
                )
                fw_metadata.num_mutated_inp_runtime_indices += 1
            i += 1

        # We add nodes corresponding to buffer assignments as output nodes in the graph.
        add_nodes = []
        output_node = list(fw_module.graph.nodes)[-1]
        for name in assigned_buffers.values():  # type: ignore[possibly-undefined]
            for node in fw_module.graph.nodes:
                if node.name == name:
                    add_nodes.append(node)
                    node.users[output_node] = None
        output_node.args = ((*add_nodes, *output_node.args[0]),)

        hook.remove()  # type: ignore[possibly-undefined]

    # As long as we opted to remove input mutations, then
    # there should be *NO* mutating ops in the graph at this point.
    if not aot_config.disable_functionalization:
        copy_count = assert_functional_graph(fw_module.graph)
        assign_epilogue_copy_streams(fw_module)
        # Wrap sync nodes with control_deps to prevent reordering
        wrap_all_sync_nodes_with_control_deps(fw_module)
        # Populate fw_metadata with stream indices from the compiled graph
        populate_fw_metadata_with_stream_indices(fw_module, fw_metadata)
        fw_module.graph.eliminate_dead_code()
        fw_module.recompile()
        copy_count2 = assert_functional_graph(fw_module.graph)
        propagate_input_mutation_stacktraces(fw_module.graph)
        if copy_count != copy_count2:
            raise AssertionError(
                f"copy_count={copy_count} != copy_count2={copy_count2}"
            )
    else:
        fw_module.graph.eliminate_dead_code()

    # See Note [Side-Effectful Tokens in AOTAutograd]
    num_tokens = len(fw_metadata.tokens)
    if num_tokens != 0 and config.unlift_effect_tokens:
        unlift_tokens(fw_module, fw_metadata, aot_config)
        saved_updated_flat_args_subclasses_desugared = (
            saved_updated_flat_args_subclasses_desugared[num_tokens:]
        )
        saved_updated_flat_args_subclasses_desugared_descs = (
            saved_updated_flat_args_subclasses_desugared_descs[num_tokens:]
        )

    if aot_config.enable_log:
        aot_graphs_log.info(
            "%s",
            lazy_format_graph_code(
                "Forward graph",
                fw_module,
                aot_config.aot_id,
                include_stride=True,
                include_device=True,
                colored=True,
                # For more expanded output set this to True (but can't default
                # to this because it affects tests):
                expanded_def=False,
            ),
        )

        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "aot_forward_graph_fw_metadata",
                "encoding": "string",
            },
            payload_fn=lambda: dataclass_repr(fw_metadata),
        )
        if maybe_subclass_meta is not None:
            trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": "aot_forward_graph_fw_subclass_metadata",
                    "encoding": "string",
                },
                payload_fn=lambda: dataclass_repr(maybe_subclass_meta),
            )

        trace_structured(
            "aot_inference_graph",
            payload_fn=lambda: fw_module.print_readable(
                print_output=False,
                include_stride=True,
                include_device=True,
                expanded_def=True,
            ),
        )

    # TODO: should factor this into a separate function for export that always only returns just the graph.
    if aot_config.is_export and maybe_subclass_meta is not None:
        raise AssertionError(
            "aot_export_module does not support tensor subclass inputs for now."
        )
    return (
        fw_module,
        saved_updated_flat_args_subclasses_desugared,
        saved_updated_flat_args_subclasses_desugared_descs,
        maybe_subclass_meta,
    )