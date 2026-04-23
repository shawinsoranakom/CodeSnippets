def maybe_realign_inputs(
    ran_cudagraphs: BoxedBool,
    compiled_graph: CompiledFxGraph,
    inputs_to_check: Sequence[int],
    mutated_inputs_idxs: OrderedSet[int],
) -> None:
    """
    Realigns input strides from inputs_to_check if
    we didn't end up running cudagraphs. Mutates
    `compiled_graph.current_callable` if cudagraphs
    was run. Otherwise, does nothing.

    Non-mutated inputs are handled by deferred alignment copies
    in the generated code. Only mutated inputs need the wrapper
    for writeback.
    """
    if not ran_cudagraphs:
        check_idxs = inputs_to_check
        if compiled_graph._defers_input_alignment:
            # Non-mutated inputs are handled by deferred alignment copies
            # in the generated Python code. Only mutated inputs need the wrapper
            # for writeback. Backends that don't emit deferred copies (cpp_wrapper,
            # FXIR) need the full wrapper.
            check_idxs = [i for i in inputs_to_check if i in mutated_inputs_idxs]
        if check_idxs:
            assert compiled_graph.current_callable is not None
            new_callable = align_inputs_from_check_idxs(
                compiled_graph.current_callable,
                check_idxs,
                mutated_inputs_idxs,
            )
            if new_callable is not compiled_graph.current_callable:
                compiled_graph.current_callable = new_callable