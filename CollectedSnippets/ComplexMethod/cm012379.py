def autotune_custom_op(
    name: str,
    decompositions: list[Callable[..., Any]],
    inputs: list[torch.fx.Node],
    non_tensor_args: list[dict[str, Any]],
    op_overload: torch._ops.OpOverload,
    user_input_gen_fns: dict[str, Callable[[torch.Tensor], torch.Tensor]] | None = None,
    config_patches_list: list[dict[str, Any]] | None = None,
    min_speedup_threshold: float = 1.0,
    benchmark_with_cudagraphs: bool = False,
) -> tuple[TensorBox, ChoiceCaller]:
    """Autotune custom operations by comparing multiple decomposition implementations.

    Currently supports SINGLE OUTPUT custom ops only.
    TODO: Add support for multiple output custom ops (tuple/list returns).

    This function generates multiple implementation choices for a custom operation and
    uses Inductor's autotuning system to select the best performing variant at runtime.
    After selecting the best choice, applies inline fusion if the winning choice has a graph.

    Args:
        name: Unique identifier for the autotuning operation
        decompositions: List of alternative implementation functions to benchmark
        inputs: Input tensor IR nodes from compilation (TensorBox/Buffer objects)
        non_tensor_args: List of kwargs dicts, paired with corresponding decompositions arg
        op_overload: OpOverload of the custom op, used as fallback implementation
        user_input_gen_fns: Optional custom input generators for benchmarking.
                           Maps input indices to functions that take fake tensors
                           and return real tensors for performance measurement.

    Returns:
        Tuple of (IR node representing the optimized operation result, winning ChoiceCaller)

    Raises:
        TypeError: If decompositions is not a list/tuple
        RuntimeError: If no inputs or no valid choices generated
    """
    if not isinstance(decompositions, (list, tuple)):
        raise TypeError(
            f"decompositions must be a list or tuple of callables, got {type(decompositions)}"
        )

    if not inputs:
        raise RuntimeError(f"Custom op '{name}' requires tensor inputs for autotuning")

    if len(decompositions) != len(non_tensor_args):
        raise ValueError(
            f"decompositions and non_tensor_args must have same length, "
            f"got {len(decompositions)} decompositions and {len(non_tensor_args)} kwargs"
        )

    # Convert user input generation functions BEFORE creating choices
    input_gen_fns: dict[int, Callable[[Any], torch.Tensor]] = {}
    if user_input_gen_fns:
        input_gen_fns = _adapt_user_input_gen_fns(
            inputs, op_overload, user_input_gen_fns
        )

    template = SubgraphTemplate(name=name)
    choices = template.generate_custom_op_choices(
        name=name,
        decompositions=decompositions,
        # pyrefly: ignore [bad-argument-type, no-matching-overload]
        input_nodes=list(inputs),
        non_tensor_args=non_tensor_args,
        input_gen_fns=input_gen_fns if input_gen_fns else None,
        config_patches_list=config_patches_list,
    )

    # Add fallback choice that calls the op eagerly (not through inductor lowering)
    # This provides a baseline to compare decompositions against
    from torch._inductor import config

    fallback_kwargs = non_tensor_args[0] if non_tensor_args else {}

    with V.fake_mode:
        # pyrefly: ignore [no-matching-overload]
        fake_inputs = [ir_node_to_tensor(inp) for inp in inputs]
        fake_output = op_overload(*fake_inputs, **fallback_kwargs)

    output_size = tuple(convert_symint_to_expr(s) for s in fake_output.shape)
    output_stride = tuple(convert_symint_to_expr(s) for s in fake_output.stride())

    fallback_choice = _create_fallback_choice(op_overload)
    fallback_choice.maybe_append_choice(
        choices=choices,
        input_nodes=list(inputs),
        layout=FixedLayout(
            device=fake_output.device,
            dtype=fake_output.dtype,
            size=output_size,
            stride=output_stride,
        ),
        **fallback_kwargs,
    )

    if not choices:
        raise RuntimeError(f"No valid choices generated for {name}")

    is_collective = _detect_collective_ops(choices)

    # Run autotuning and get both result and winning choice
    selected_result, winning_choice = autotune_select_algorithm(
        name=name,
        choices=choices,
        input_nodes=list(inputs),
        layout=choices[0].layout,
        input_gen_fns=input_gen_fns,
        is_collective=is_collective,
        min_speedup_threshold=min_speedup_threshold,
        benchmark_with_cudagraphs=benchmark_with_cudagraphs,
    )

    # Test mode: force specific choice to win
    force_choice = config.test_configs.force_custom_op_decomposition
    if force_choice is True and winning_choice.gm is None:
        # Force decomposition: pick first choice with a graph
        for choice in choices:
            if choice.gm is not None:
                log.info(
                    "Test mode: forcing decomposition %s over fallback",
                    getattr(choice, "name", type(choice).__name__),
                )
                winning_choice = choice
                selected_result = choice.output_node()
                break
    elif force_choice is False and winning_choice.gm is not None:
        # Force fallback: pick first choice without a graph
        for choice in choices:
            if choice.gm is None:
                log.info(
                    "Test mode: forcing fallback %s over decomposition",
                    getattr(choice, "name", type(choice).__name__),
                )
                winning_choice = choice
                selected_result = choice.output_node()
                break

        # Always inline when winning_choice has a graph; callers extract choice metadata separately
    if winning_choice.gm is not None:
        log.debug(
            "Inlining winning choice: %s (name=%s)",
            getattr(winning_choice, "name", type(winning_choice).__name__),
            name,
        )
        from torch._inductor.codegen.subgraph import inline_subgraph_to_ir_nodes

        ops_before = len(V.graph.operations)
        result = inline_subgraph_to_ir_nodes(winning_choice.gm, inputs, name)

        # Tag inlined operations with config_patches from the winning choice
        config_patches = winning_choice.config_patches
        if config_patches:
            for op in V.graph.operations[ops_before:]:
                op.set_config_patches(config_patches.copy())

        return result, winning_choice

    log.debug(
        "Winning choice does not support inlining: %s (name=%s)",
        getattr(winning_choice, "name", type(winning_choice).__name__),
        name,
    )
    return selected_result, winning_choice