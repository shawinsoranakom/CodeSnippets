def cudagraph_partition_post_compile(
    example_inputs: Sequence[InputType],
    compiled_graph: CompiledFxGraph,
    cudagraphs: BoxedBool,
    constants: dict[str, torch.Tensor | type],
    boxed_forward_device_index: BoxedDeviceIndex | None,
) -> None:
    """
    Cudagraphify each partition functions, which first prepares the necessary
    metadata and then applies the cudagraphify function to each partition.

    Assuming all partition functions are cudagraphified and share the same order
    as `compiled_graph.partition_maps`. See [Note: Graph Partition Map for CUDAGraph].
    """
    from torch._inductor.compiler_bisector import CompilerBisector

    if CompilerBisector.disable_subsystem("inductor", "cudagraphs"):
        BoxedBool.disable(cudagraphs)
        maybe_handle_backward_generation(compiled_graph, boxed_forward_device_index)
        log_cudagraph_skip_and_bump_counter("skipping cudagraphs due to bisector")
        return

    assert compiled_graph.cudagraph_info is not None
    cudagraph_fail_reasons = compiled_graph.cudagraph_info.cudagraph_fail_reasons

    if (
        cudagraph_fail_reasons
        or compiled_graph.partition_maps is None
        or len(compiled_graph.partition_maps) == 0
    ):
        # cudagraphify is not called if there are no partitions
        BoxedBool.disable(cudagraphs)
        maybe_handle_backward_generation(compiled_graph, boxed_forward_device_index)
        return

    assert compiled_graph.current_callable is not None
    assert compiled_graph.recursively_apply_fns is not None
    is_inference = compiled_graph.fx_kwargs["is_inference"]
    is_backward = compiled_graph.fx_kwargs["is_backward"]
    static_input_idxs = OrderedSet(compiled_graph.fx_kwargs["static_input_idxs"] or ())
    mutated_input_idxs = compiled_graph.mutated_input_idxs
    device_index = next(iter(compiled_graph.device_idxs))

    # Filter to only tensor constants (exclude opaque value type classes)
    tensor_constants = {
        k: v for k, v in constants.items() if isinstance(v, torch.Tensor)
    }

    assert compiled_graph.cudagraph_info.stack_traces is not None, (
        "stack_traces should not be None in cudagraph_partition_post_compile"
    )
    graph_metadata = CudagraphMetadata(
        compiled_graph.cudagraph_info.placeholders,
        static_input_idxs,
        mutated_input_idxs,
        compiled_graph.cudagraph_info.stack_traces,
        tensor_constants,
    )

    prepare_cudagraph_post_compile(
        compiled_graph, example_inputs, boxed_forward_device_index
    )

    from .compile_fx import cudagraphify

    # cudagraphify each partition function, assuming every graph partition function
    # is cudagraphable. Non-cudagraphable ops (e.g., cpu ops) are inlined into
    # `call` function and not included in partition functions.
    cudagraphify_fns = []
    for partition_map in compiled_graph.partition_maps:
        partition_metadata = get_partition_cudagraph_metadata(
            partition_map,
            graph_metadata,
        )

        cudagraphify_fn = partial(
            cudagraphify,
            static_input_idxs=tuple(partition_metadata.static_input_idxs),
            device_index=device_index,
            stack_traces=partition_metadata.stack_traces,
            is_backward=is_backward,
            is_inference=is_inference,
            constants=tuple(partition_metadata.constants.values()),
            placeholders=partition_metadata.placeholders,
            mutated_input_idxs=tuple(partition_metadata.mutated_input_idxs),
        )
        cudagraphify_fns.append(cudagraphify_fn)

    compiled_graph.recursively_apply_fns(cudagraphify_fns)