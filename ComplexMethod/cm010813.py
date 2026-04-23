def _try_get_metadata_from_dynamo(
    mod: torch.nn.Module,
    param_keys: KeysView[str],
    full_args_num: int,
    full_args_descs: list[DifferentiableAOTInput],
) -> tuple[list[torch._guards.Source | None] | None, list[int]]:
    """
    Metadata is forwarded from Dynamo to AOTDispatch via special fields on GraphModule.
    We first verify that `mod` does come from Dynamo, then we handle cases where
    metadata might be missing.

    Returns:
        aot_autograd_arg_pos_to_source: used to dedup params and their guards
        static_input_indices: used to identify static inputs for cudagraphs
    """
    # Note [Assumption on Dynamo Metadata]
    # This function assumes a graph module from dynamo provides `dynamo_compiled_id`,
    # _param_name_to_source, and every placeholder node has `_dynamo_source` attributes.
    # When gm is modified (e.g., DDPOptimizer via split_module), metadata needs to
    # be propagated in order to be recognized as a dynamo graph

    if not (isinstance(mod, torch.fx.GraphModule) and "dynamo_compile_id" in mod.meta):
        # graph was not captured by dynamo
        return None, []

    if not hasattr(mod, "_param_name_to_source"):
        # is from export
        static_input_indices = [
            i
            for i, node in enumerate(full_args_descs)
            if isinstance(node, (ParamAOTInput, BufferAOTInput))
        ]
        return None, static_input_indices

    # We now know this came from dynamo, and (1) we care about guards,
    # so setting up aot_autograd_arg_pos_to_source for downstream dedup guards
    # can now be done safely. (2) Dynamo logic protects the 1:1 sizing below.
    # Additionally, we mark static indices for cudagraphs.
    param_name_to_source = cast(
        dict[str, torch._guards.Source], mod._param_name_to_source
    )
    seen_sources = set()

    aot_autograd_arg_pos_to_source: list[torch._guards.Source | None] = []
    static_input_indices = []
    # Collect the new inputs lifted by aotdispatch
    for i, name in enumerate(param_keys):
        if name not in param_name_to_source:
            raise AssertionError(f"{name} not found in param_name_to_source")
        source = param_name_to_source[name]
        if source in seen_sources:
            raise AssertionError(f"source {source} already in seen_sources")
        if source is None:
            raise AssertionError(f"source must not be None for {name}")
        seen_sources.add(source)
        aot_autograd_arg_pos_to_source.append(source)

        static_input_indices.append(i)

    # Collect the dynamo graph inputs
    # TODO(mlazos): Revisit if this is still needed. With Dynamo install ID
    # matched tensors back into the Fx graph, this might not be necessary.
    for pos, node in enumerate(mod.graph.find_nodes(op="placeholder")):
        if not hasattr(node, "_dynamo_source"):
            raise AssertionError(f"node {node} must have _dynamo_source attribute")
        source = node._dynamo_source
        # `source`` specifies the source from user code. ddp optimizer may have
        # intermediate values becoming submodule placeholders which does not
        # have a source
        if source is not None and source in seen_sources:
            raise AssertionError(f"source {source} already in seen_sources")
        seen_sources.add(source)
        aot_autograd_arg_pos_to_source.append(source)
        source_name = source.name if source else str(source)

        # input[i] in dynamo is now:
        # input[i + len(extra_params)] in AOT,
        # where extra_params are the params/buffers that dynamo baked into the
        # OutputGraph
        actual_pos = pos + len(param_keys)

        if "tensor_dict" in node.meta and node.meta["tensor_dict"].get(
            "_dynamo_static_input_type", None
        ):
            static_inputs_log.debug(
                "Adding static input pos %s for source %s", actual_pos, source_name
            )
            static_input_indices.append(actual_pos)
        else:
            static_inputs_log.debug(
                "Non-static input pos %s for source %s", actual_pos, source_name
            )

    if full_args_num != len(aot_autograd_arg_pos_to_source):
        raise AssertionError(
            f"full_args_num={full_args_num} != len(aot_autograd_arg_pos_to_source)={len(aot_autograd_arg_pos_to_source)}"
        )
    return aot_autograd_arg_pos_to_source, static_input_indices