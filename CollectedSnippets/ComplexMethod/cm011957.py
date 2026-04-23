def fw_compiler_freezing(
    aot_autograd_model: GraphModule,
    aot_example_inputs: Sequence[InputType],
    dynamo_model: GraphModule,
    num_example_inputs: int,
    inner_compile: Callable[..., Any],
    # TODO: Take compiler_config_extra instead
    cudagraphs: BoxedBool,
    graph_id: int,
    forward_device: BoxedDeviceIndex,
) -> Callable[[list[object]], Sequence[torch.Tensor]]:
    from torch._inductor.freezing import convert_conv_weights_to_channels_last, freeze

    # partition_fn won't be called
    inputs_devices = get_inputs_devices(aot_example_inputs, aot_autograd_model)
    aot_autograd_model = _recursive_joint_graph_passes(
        aot_autograd_model,
        input_device=next(iter(inputs_devices)),
    )

    layout_opt = GraphLowering.decide_layout_opt(aot_autograd_model, is_inference=True)
    if layout_opt:
        # make sure meta['val'] is properly setup
        fake_tensor_prop(aot_autograd_model, aot_example_inputs, True)
        convert_conv_weights_to_channels_last(aot_autograd_model)

    opt_model, preserved_arg_indices = freeze(
        dynamo_model,
        aot_autograd_model,
        aot_example_inputs,  # type: ignore[arg-type]
    )

    aot_example_inputs = [aot_example_inputs[ind] for ind in preserved_arg_indices]

    fake_mode = detect_fake_mode(aot_example_inputs)

    # for freezing, all graph outputs should be user visible
    *_, model_outputs_node = opt_model.graph.nodes
    model_outputs = model_outputs_node.args[0]
    model_outputs_node.meta["user_visible_output_idxs"] = [
        idx for idx, n in enumerate(model_outputs) if isinstance(n, torch.fx.Node)
    ]

    static_input_idxs: list[Any] = []
    # constant params will be real tensors, not fake
    tracing_context = torch._guards.TracingContext.try_get()
    unwrapped_args_offsets = [0]
    max_offset_idx = 0
    if tracing_context is not None:
        assert tracing_context.params_flat_unwrap_subclasses is not None
        params_flat_unwrap = tracing_context.params_flat_unwrap_subclasses
        max_offset_idx = max(0, len(params_flat_unwrap) - 1)
        preserved_indices_params_flat = OrderedSet[int]()
        unwrapped_idxs = tracing_context.params_unwrapped_to_flat_index
        assert unwrapped_idxs is not None
        current_offset = 0
        if len(params_flat_unwrap) > 0:
            unwrapped_args_offsets = []

        for i in range(len(params_flat_unwrap)):
            if i not in preserved_arg_indices:
                params_flat_unwrap[i] = None
                if i > 0 and unwrapped_idxs[i] == unwrapped_idxs[i - 1]:
                    current_offset += 1
            else:
                preserved_indices_params_flat.add(unwrapped_idxs[i])
            unwrapped_args_offsets.append(current_offset)

        # Deallocate wrapped params, if all subelements were deallocated
        assert tracing_context.params_flat is not None
        for i in range(len(tracing_context.params_flat)):
            if i not in preserved_indices_params_flat:
                tracing_context.params_flat[i] = None

        if tracing_context.fw_metadata:
            static_input_idxs = tracing_context.fw_metadata.static_input_indices

    with mock.patch.object(fake_mode, "allow_non_fake_inputs", True):
        optimized_function = inner_compile(
            opt_model,
            aot_example_inputs,
            static_input_idxs=static_input_idxs,
            cudagraphs=cudagraphs,
            graph_id=graph_id,
            is_inference=True,
            boxed_forward_device_index=forward_device,
            layout_opt=layout_opt,
        )

    # aot_inductor codegens a call that takes in just the inputs, so we don't return a wrapper
    # that drops constant-ified params
    if V.aot_compilation:
        return optimized_function

    def wrapper(args: list[object]) -> Sequence[torch.Tensor]:
        args_new = [
            args[i - unwrapped_args_offsets[min(i, max_offset_idx)]]
            for i in preserved_arg_indices
        ]
        args.clear()
        return optimized_function(args_new)

    wrapper._boxed_call = True  # type: ignore[attr-defined]

    return wrapper