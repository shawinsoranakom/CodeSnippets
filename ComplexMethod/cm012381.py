def _range_based_lowering_fn(
    processed_configs: list[CustomOpConfig],
    default_impl: Callable[..., Any],
    name: str,
    op_overload: torch._ops.OpOverload,
    input_gen_fns: dict[str, Callable[[torch.Tensor], torch.Tensor]] | None,
    tensor_name: str,
    dim_index: int,
    ranges: list[tuple[int, int | float]],
    tensor_inputs: list[Any],
    runtime_kwargs: dict[str, Any],
    range_upper_bound: int,
    config_generator: Callable[[dict[str, torch.Tensor]], list[CustomOpConfig]]
    | None = None,
    min_speedup_threshold: float = 1.0,
    benchmark_with_cudagraphs: bool = False,
) -> Any:
    """Range-based autotuning lowering function."""
    from torch._inductor.codegen.subgraph import inline_subgraph_to_ir_nodes
    from torch.fx.experimental.proxy_tensor import make_fx

    from ..decomposition import select_decomp_table

    log.info("=== Range-based Autotuning for %s ===", name)
    log.info("Dispatch on: %s[%d], Ranges: %s", tensor_name, dim_index, ranges)

    decompositions, non_tensor_args, config_patches_list = (
        _prepare_configs_and_decompositions(
            processed_configs,
            config_generator,
            tensor_inputs,
            default_impl,
            op_overload,
            runtime_kwargs,
            name,
        )
    )

    range_to_best_impl_map: dict[RangeBounds, ImplConfig] = {}

    # Benchmark each range and collect winning implementations
    for range_start, range_end in ranges:
        if input_gen_fns and tensor_name in input_gen_fns:
            base_gen_fn = input_gen_fns[tensor_name]
        else:
            base_gen_fn = _default_input_gen_fn

        range_gen_fn = _create_range_input_gen_fn(
            base_gen_fn, dim_index, range_start, range_end, range_upper_bound
        )
        range_input_gen_fns = {**(input_gen_fns or {}), tensor_name: range_gen_fn}

        range_name = f"{name}_range_{int(range_start)}_{int(range_end) if range_end != float('inf') else 'inf'}"

        # pyrefly: ignore [not-iterable]
        autotuned_result, winning_choice = autotune_custom_op(
            name=range_name,
            decompositions=decompositions,
            inputs=tensor_inputs,
            non_tensor_args=non_tensor_args,
            op_overload=op_overload,
            user_input_gen_fns=range_input_gen_fns,
            min_speedup_threshold=min_speedup_threshold,
            benchmark_with_cudagraphs=benchmark_with_cudagraphs,
            config_patches_list=config_patches_list,
        )

        if winning_choice.decomposition is not None:
            winning_impl = winning_choice.decomposition
            winning_kwargs = winning_choice.decomposition_kwargs
        else:
            # Fallback was selected (ExternKernelCaller)
            winning_impl = default_impl
            winning_kwargs = non_tensor_args[0] if non_tensor_args else {}
            log.info(
                "   Range [%s, %s]: Fallback (default_impl) selected",
                range_start,
                range_end if range_end != float("inf") else "inf",
            )

        winning_config_patches = winning_choice.config_patches or {}

        # Create dataclass instances for cleaner code
        range_bounds = RangeBounds(range_start, range_end)
        impl_config = ImplConfig(
            impl_name=winning_impl.__name__,
            impl_func=winning_impl,
            kwargs=winning_kwargs,
            config_patches=winning_config_patches,
        )
        range_to_best_impl_map[range_bounds] = impl_config

        log.info(
            "   Range %s -> %s",
            range_bounds,
            impl_config.impl_name,
        )

    # Group ranges by implementation
    from torch.fx.experimental.symbolic_shapes import _ShapeEnvGuardError

    impl_groups = _group_ranges_by_impl(range_to_best_impl_map)

    log.info("After grouping by implementation: %d impl groups", len(impl_groups))
    for group in impl_groups:
        log.info("   %s", group)

    # If only one impl group remains, just inline that implementation
    if len(impl_groups) == 1:
        group = impl_groups[0]
        log.info("Only one implementation after grouping, directly inlining")
        return _lower_single_impl(
            group.impl_func,
            group.impl_kwargs,
            runtime_kwargs,
            tensor_inputs,
            name,
            config_patches=group.config_patches,
        )

    def dispatch_fn(*fake_tensors):
        """Build nested torch.cond dispatch: cond(pred1, impl1, cond(pred2, impl2, ...))."""
        num_impl_groups = len(impl_groups)
        if num_impl_groups < 2:
            raise RuntimeError(
                f"dispatch_fn requires at least 2 impl groups, got {num_impl_groups}"
            )

        dim_value = fake_tensors[0].size(dim_index)

        def build_range_predicate(ranges_list: list[RangeBounds]) -> torch.Tensor:
            predicates = []
            for rb in ranges_list:
                end = int(rb.end) if rb.end != float("inf") else None
                if end is None:
                    predicates.append(dim_value >= rb.start)
                else:
                    predicates.append((dim_value >= rb.start) & (dim_value <= end))

            result = predicates[0]
            for pred in predicates[1:]:
                result = result | pred
            return result  # pyrefly: ignore [bad-return]

        def build_nested_cond(idx: int):
            if idx >= num_impl_groups:
                raise RuntimeError(f"Invalid impl group index: {idx}")

            group = impl_groups[idx]
            merged_kwargs = _merge_config_and_runtime_kwargs(
                group.impl_kwargs, runtime_kwargs
            )

            @torch._dynamo.dont_skip_tracing
            def group_fn(*ops):
                return group.impl_func(*ops, **merged_kwargs)

            if idx == num_impl_groups - 1:
                return group_fn

            next_fn = build_nested_cond(idx + 1)

            @torch._dynamo.dont_skip_tracing
            def cond_wrapper(*ops, _ranges=group.ranges):
                return torch.cond(
                    pred=build_range_predicate(_ranges),
                    true_fn=group_fn,
                    false_fn=next_fn,
                    operands=ops,
                )

            return cond_wrapper

        return build_nested_cond(0)(*fake_tensors)

    with V.fake_mode:
        fake_inputs = tuple(ir_node_to_tensor(inp) for inp in tensor_inputs)
        decomposition_table = select_decomp_table()
        shape_env = V.fake_mode.shape_env

        log.info("Tracing torch.cond dispatch with symbolic shapes...")

        try:
            context = (
                shape_env.error_on_new_guards
                if shape_env is not None
                else contextlib.nullcontext
            )
            with context():
                dispatch_gm = make_fx(
                    dispatch_fn,
                    decomposition_table=decomposition_table,
                    tracing_mode="symbolic",
                )(*fake_inputs)

            log.info("Successfully traced torch.cond dispatch")
            log.info("Traced graph:\n%s", dispatch_gm.graph)

        except (_ShapeEnvGuardError, AssertionError) as e:
            is_guard_error = isinstance(e, _ShapeEnvGuardError) or (
                isinstance(e, AssertionError)
                and "Guard attempted while ShapeEnv guards are frozen" in str(e)
            )
            if not is_guard_error:
                raise
            log.info("Dispatch function adds guards, skipping custom op lowering")
            counters["inductor"]["custom_op_decomp_guard_skips"] += 1
            return None

        except Exception:
            log.exception("make_fx tracing FAILED")
            raise

    ops_before = len(V.graph.operations)
    result = inline_subgraph_to_ir_nodes(dispatch_gm, tensor_inputs, f"{name}_dispatch")

    # Apply config_patches from all impl groups to inlined operations
    # TODO - consider conflicting patches
    merged_patches: dict[str, Any] = {}
    for group in impl_groups:
        merged_patches.update(group.config_patches)
    if merged_patches:
        _apply_config_patches_recursive(V.graph.operations[ops_before:], merged_patches)

    log.info(
        "Successfully created torch.cond dispatch for %d impl groups", len(impl_groups)
    )

    validate_ir(result)
    return result