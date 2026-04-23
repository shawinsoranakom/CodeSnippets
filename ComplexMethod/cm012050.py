def cudagraph_post_compile(
    example_inputs: Sequence[InputType],
    compiled_graph: CompiledFxGraph,
    cudagraphs: BoxedBool,
    constants: dict[str, torch.Tensor | type],
    boxed_forward_device_index: BoxedDeviceIndex | None,
) -> None:
    """
    Checks for any reasons not to run cudagraphs and then
    runs it on compiled_graph.
    Mutates the `compiled_graph.current_callable` and `cudagraphs`
    """
    from torch._inductor.compiler_bisector import CompilerBisector

    assert compiled_graph.current_callable is not None
    assert compiled_graph.cudagraph_info is not None
    cached_info = compiled_graph.cudagraph_info
    cudagraph_fail_reasons = cached_info.cudagraph_fail_reasons
    is_inference = compiled_graph.fx_kwargs["is_inference"]
    is_backward = compiled_graph.fx_kwargs["is_backward"]

    # Check if bisector wants to disable cudagraphs for this graph
    if CompilerBisector.disable_subsystem("inductor", "cudagraphs"):
        BoxedBool.disable(cudagraphs)
        maybe_handle_backward_generation(compiled_graph, boxed_forward_device_index)
        log_cudagraph_skip_and_bump_counter("skipping cudagraphs due to bisector")
        return

    if not cudagraph_fail_reasons:
        fx_kwargs = compiled_graph.fx_kwargs
        static_input_idxs = fx_kwargs["static_input_idxs"]

        placeholders = cached_info.placeholders
        stack_traces = cached_info.stack_traces
        assert stack_traces is not None, (
            "stack_traces should not be None in cudagraph_post_compile"
        )

        prepare_cudagraph_post_compile(
            compiled_graph, example_inputs, boxed_forward_device_index
        )

        current_callable = compiled_graph.current_callable
        assert current_callable is not None
        # Filter to only tensor constants (exclude opaque value type classes)
        tensor_constants = {
            k: v for k, v in constants.items() if isinstance(v, torch.Tensor)
        }

        device_index = next(iter(compiled_graph.device_idxs))
        cudagraphify_kwargs = dict(
            device_index=device_index,
            stack_traces=stack_traces,
            is_backward=is_backward,
            is_inference=is_inference,
            constants=tuple(tensor_constants.values()),
            placeholders=placeholders,
            mutated_input_idxs=tuple(compiled_graph.mutated_input_idxs),
        )

        policy = config.cudagraph_policy
        if policy is not None:
            compiled_graph.current_callable = policy.cudagraphify(
                current_callable,
                example_inputs,
                static_input_idxs or (),
                **cudagraphify_kwargs,
            )
        else:
            from .compile_fx import cudagraphify

            compiled_graph.current_callable = cudagraphify(
                current_callable,
                static_input_idxs=static_input_idxs or (),
                **cudagraphify_kwargs,
            )

    else:
        BoxedBool.disable(cudagraphs)
        maybe_handle_backward_generation(compiled_graph, boxed_forward_device_index)

        if "cuda" in compiled_graph.device_types:
            # prefer better disable_cudagraphs_reason bc stack trace
            # TODO: migrate all disable reasons to stack trace, refactor
            if compiled_graph.disabled_cudagraphs_reason:
                log_cudagraph_skip_and_bump_counter(
                    compiled_graph.disabled_cudagraphs_reason
                )
            else:
                log_cudagraph_skip_and_bump_counter(
                    f"skipping cudagraphs due to {cudagraph_fail_reasons}"
                )