def compile_fx_forward(
    gm: GraphModule,
    example_inputs: Sequence[InputType],
    num_orig_model_outputs: int,
    num_example_inputs: int,
    compiler_config_extra: CompilerConfigExtra,
    inner_compile: Callable[..., OutputCode] = compile_fx_inner,
    is_inference: bool = False,
) -> OutputCode:
    """
    Compile the forward graph of the given graph module.

    Args:
        gm: The graph module to compile.
        example_inputs: The example inputs to use for compilation.
        num_orig_model_outputs: The number of model outputs from the original dynamo graph.
        num_example_inputs: The number of example inputs from the original dynamo graph.
        compiler_config_extra: Extra configuration for the compiler.
        inner_compile: The inner compile function to use.
        is_inference: Whether this is an inference graph.
    """

    if is_inference:
        # partition_fn won't be called
        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "before_joint_graph",
                "encoding": "string",
            },
            payload_fn=lambda: gm.print_readable(
                print_output=False, include_stride=True, include_device=True
            ),
        )

        # Snapshot stack traces on the output node before passes run,
        # as later passes may strip stack_trace from individual nodes.
        output = output_node(gm)
        output.meta["output_stack_traces"] = [
            (
                arg.meta.get("stack_trace")
                if isinstance(arg, torch.fx.node.Node)
                else None
            )
            for arg in output.args[0]  # type: ignore[union-attr]
        ]

        inputs_devices = get_inputs_devices(example_inputs, gm)
        gm = _recursive_joint_graph_passes(gm, input_device=next(iter(inputs_devices)))

        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "after_joint_graph",
                "encoding": "string",
            },
            payload_fn=lambda: gm.print_readable(
                print_output=False, include_stride=True, include_device=True
            ),
        )

    fixed = torch._inductor.utils.num_fw_fixed_arguments(
        num_example_inputs, len(example_inputs)
    )

    model_outputs_node = output_node(gm)
    if config.keep_output_stride:
        model_outputs = pytree.arg_tree_leaves(*model_outputs_node.args)
        num_model_outputs = len(model_outputs)

        context = torch._guards.TracingContext.try_get()
        # See Note [User Outputs in the inductor graph]
        if context is not None and context.fw_metadata and not is_inference:
            original_output_start_index = (
                context.fw_metadata.num_mutated_inp_runtime_indices
            )
        else:
            original_output_start_index = 0

        assert num_orig_model_outputs <= num_model_outputs

        # Note [User Outputs in the inductor graph]
        # We makes the following assumption
        # For inference
        #   len(orig_model_outputs) == len(model_outputs)
        # For training
        #   len(orig_model_outputs) <= len(model_outputs)
        # During training, most of the time the model_outputs starts with
        # original module's outputs followed by saved activations.
        # But this can be not true if the model have inplace updated tensors.
        # AOTAutograd will make those tensors being returned before the original
        # module's output.
        # To make things safe, we'll use original_output_start_index field
        # set by AOTAutograd to decide where the original module outputs start.
        orig_output_end_idx = original_output_start_index + num_orig_model_outputs
        # Sanity check: we are about to splice out the "user" outputs from the full set
        # of "graph" outputs. Make sure we're within bounds.
        assert orig_output_end_idx <= num_model_outputs

        model_outputs_node.meta["user_visible_output_idxs"] = [
            idx
            for idx in range(original_output_start_index, orig_output_end_idx)
            if isinstance(model_outputs[idx], torch.fx.Node)
        ]
    else:
        model_outputs_node.meta["user_visible_output_idxs"] = []

    # We also mark the invoke_subgraph outputs as user_visible to
    # force the outputs of invoke_subgraph subgraph to follow the
    # original strides
    _recursive_record_user_visible_output_idxs(gm)

    with cudagraph_annotation_context(compiler_config_extra.cudagraphs):
        result = inner_compile(
            gm,
            example_inputs,
            static_input_idxs=get_static_input_idxs(fixed),
            cudagraphs=compiler_config_extra.cudagraphs,
            graph_id=compiler_config_extra.graph_id,
            is_inference=is_inference,
            boxed_forward_device_index=compiler_config_extra.forward_device,
        )

        if (
            not is_inference
            and isinstance(result, CompiledFxGraph)
            and result.partition_maps
            and len(result.partition_maps) > 1
        ):
            compiler_config_extra.forward_is_partitioned.value = True

        return result