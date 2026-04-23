def _lower_single_impl(
    impl: Callable[..., Any],
    impl_kwargs: dict[str, Any],
    runtime_kwargs: dict[str, Any],
    tensor_inputs: list[Any],
    name: str,
    config_patches: dict[str, Any] | None = None,
) -> Any:
    """Lower a single implementation by tracing and inlining it.

    Uses error_on_new_guards() during tracing to detect if the impl adds guards.
    Returns None if the impl adds guards, signaling caller to skip this choice.
    """
    from torch._inductor.codegen.subgraph import inline_subgraph_to_ir_nodes
    from torch.fx.experimental.proxy_tensor import make_fx
    from torch.fx.experimental.symbolic_shapes import _ShapeEnvGuardError

    from ..decomposition import select_decomp_table

    merged_kwargs = _merge_config_and_runtime_kwargs(impl_kwargs, runtime_kwargs)

    def impl_wrapper(*tensors):
        return impl(*tensors, **merged_kwargs)

    shape_env = V.fake_mode.shape_env

    with V.fake_mode:
        fake_inputs = tuple(ir_node_to_tensor(inp) for inp in tensor_inputs)
        decomposition_table = select_decomp_table()

        context = (
            shape_env.error_on_new_guards
            if shape_env is not None
            else contextlib.nullcontext
        )
        try:
            with context():
                impl_gm = make_fx(
                    impl_wrapper,
                    decomposition_table=decomposition_table,
                    tracing_mode="symbolic",
                )(*fake_inputs)
        except (_ShapeEnvGuardError, AssertionError) as e:
            is_guard_error = isinstance(e, _ShapeEnvGuardError) or (
                isinstance(e, AssertionError)
                and "Guard attempted while ShapeEnv guards are frozen" in str(e)
            )
            if not is_guard_error:
                raise
            log.info(
                "Implementation %s adds guards, skipping custom op lowering",
                impl.__name__,
            )
            counters["inductor"]["custom_op_decomp_guard_skips"] += 1
            return None

    log.info("Inlining implementation: %s", impl.__name__)
    ops_before = len(V.graph.operations)
    result = inline_subgraph_to_ir_nodes(impl_gm, tensor_inputs, name)

    if config_patches:
        _apply_config_patches_recursive(V.graph.operations[ops_before:], config_patches)

    validate_ir(result)
    return result