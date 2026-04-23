def cudagraphify_impl(
    model: Callable[..., Any],
    inputs: list[torch.Tensor],
    static_input_idxs: Sequence[int] = (),
) -> Callable[[list[InputType]], Any]:
    """
    Assumes inputs[static_input_idxs[i]] are always the same memory address
    """
    check_input_idxs = get_input_idxs_to_check(inputs, static_input_idxs)  # type: ignore[arg-type]
    # pyrefly: ignore [annotation-mismatch, redefinition]
    static_input_idxs: OrderedSet[int] = OrderedSet(
        remove_unaligned_input_idxs(inputs, static_input_idxs)  # type: ignore[arg-type]
    )
    copy_misaligned_inputs(inputs, check_input_idxs)  # type: ignore[arg-type]

    assert isinstance(inputs, list)

    inps_expanded_dims = [
        get_expanded_dims(x) if idx not in static_input_idxs else []
        for idx, x in enumerate(inputs)
    ]

    # allocate static tensor inputs
    static_inputs = [
        (
            x
            if not isinstance(x, torch.Tensor)
            else static_input(x)
            if idx not in static_input_idxs
            else x.detach()
        )
        for idx, x in enumerate(inputs)
    ]

    # copy over input values for fresh allocations
    for idx, (x, expanded_dims) in enumerate(zip(inputs, inps_expanded_dims)):
        if isinstance(x, torch.Tensor) and idx not in static_input_idxs:
            index_expanded_dims_and_copy_(static_inputs[idx], x, expanded_dims)

    # warmup
    torch.cuda.synchronize()
    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())
    # copy static_inputs because it will be cleared in model
    with torch.cuda.stream(stream):
        model(list(static_inputs))
    stream.synchronize()
    torch.cuda.current_stream().wait_stream(stream)
    torch.cuda.synchronize()

    # record
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, stream=stream, capture_error_mode="thread_local"):
        static_outputs = model(list(static_inputs))
    if not isinstance(static_outputs, (list, tuple)):
        static_outputs = (static_outputs,)

    if config.size_asserts:

        def run(new_inputs: list[InputType]) -> Callable[[list[InputType]], Any]:
            assert len(static_inputs) == len(new_inputs)
            for idx, (dst, src, expanded_dims) in enumerate(
                zip(static_inputs, new_inputs, inps_expanded_dims)
            ):
                if not isinstance(dst, torch.Tensor):
                    continue
                assert isinstance(src, torch.Tensor)
                if idx in static_input_idxs:
                    assert dst.data_ptr() == src.data_ptr()
                else:
                    # TODO - could make one single op of multiple slices
                    # and avoid dispatch.
                    # Could also pre-index the `dst` tensors
                    index_expanded_dims_and_copy_(dst, src, expanded_dims)
            new_inputs.clear()
            graph.replay()
            # pyrefly: ignore [bad-return]
            return static_outputs

    else:
        copy_indices = [
            idx for idx in range(len(static_inputs)) if idx not in static_input_idxs
        ]

        def run(new_inputs: list[InputType]) -> Callable[[list[InputType]], Any]:
            for idx in copy_indices:
                expanded_dims = inps_expanded_dims[idx]
                src = new_inputs[idx]
                assert isinstance(src, torch.Tensor)
                index_expanded_dims_and_copy_(static_inputs[idx], src, expanded_dims)
            new_inputs.clear()
            graph.replay()
            # pyrefly: ignore [bad-return]
            return static_outputs

    return align_inputs_from_check_idxs(run, check_input_idxs, OrderedSet())