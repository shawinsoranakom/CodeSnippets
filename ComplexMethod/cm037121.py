def reconstruct_serializable_fn_from_mega_artifact(
    state: dict[str, Any],
    standalone_compile_artifacts: "StandaloneCompiledArtifacts",
    vllm_config: VllmConfig,
    sym_shape_indices_map: dict[str, list[int]],
    returns_tuple_map: dict[str, bool],
) -> "VllmSerializableFunction":
    """Construct a VllmSerializableFunction from cached inductor artifacts.

    This function reconstructs a callable model from pre-compiled inductor
    artifacts without re-running the compilation. It:
    1. Loads all cached artifacts
    2. Builds compiled callables for each submodule/shape
    3. Creates PiecewiseBackend instances that dispatch to cached artifacts
    4. Wraps with cudagraph if needed
    5. Returns the final VllmSerializableFunction

    Note: This function shares similar logic with PiecewiseCompileInterpreter
    in backends.py. Both create PiecewiseBackend instances and wrap them with
    cudagraph. The key difference is:
    - this function: PiecewiseBackend receives pre-compiled runnables
      (compiled_runnables is set, graph is None)
    - PiecewiseCompileInterpreter: PiecewiseBackend receives the FX graph
      to compile (graph is set, compiled_runnables is None)

    If modifying the backend creation/wrapping logic, consider updating both.

    Args:
        state: Deserialized state dict containing graph_module, example_inputs,
            prefix, sym_tensor_indices, is_encoder, etc.
        standalone_compile_artifacts: The StandaloneCompiledArtifacts containing
            pre-compiled artifacts for each submodule/shape combination.
        vllm_config: The vLLM configuration.
        sym_shape_indices_map: Mapping from submod_name to sym_shape_indices.
        returns_tuple_map: Mapping from submod_name to returns_tuple.

    Returns:
        A VllmSerializableFunction that can be called directly.
    """
    from vllm.compilation.backends import (
        VllmBackend,
        make_copy_and_call,
        wrap_with_cudagraph_if_needed,
    )
    from vllm.compilation.piecewise_backend import PiecewiseBackend

    prefix = state["prefix"]
    is_encoder = state.get("is_encoder", False)
    split_gm = state["graph_module"]
    compilation_config = vllm_config.compilation_config

    standalone_compile_artifacts.load_all()

    piecewise_submod_names = standalone_compile_artifacts.submodule_names()
    compiled_callables: dict[str, dict[str, Callable[..., Any]]] = {}

    for cache_key in standalone_compile_artifacts.submodule_bytes:
        submod_name, shape_str = cache_key.rsplit("_", 1)
        compiled_callables.setdefault(submod_name, {})[shape_str] = (
            standalone_compile_artifacts.get_loaded(submod_name, shape_str)
        )

    vllm_backend = VllmBackend(vllm_config, prefix, is_encoder)
    dummy_cache_dir = os.path.join(envs.VLLM_CACHE_ROOT, "dummy_cache")
    os.makedirs(dummy_cache_dir, exist_ok=True)
    vllm_backend.compiler_manager.initialize_cache(
        cache_dir=dummy_cache_dir,
        disable_cache=True,
        prefix=prefix,
    )

    # spot check that cached submodules exist in the graph structure
    graph_children = {name for name, _ in split_gm.named_children()}
    missing = set(piecewise_submod_names) - graph_children
    assert not missing, (
        f"artifacts reference submodules not in graph: {missing}. "
        f"graph has: {sorted(graph_children)}"
    )

    for i, submod_name in enumerate(piecewise_submod_names):
        assert submod_name in sym_shape_indices_map and submod_name in returns_tuple_map

        sym_shape_indices = sym_shape_indices_map[submod_name]
        returns_tuple = returns_tuple_map[submod_name]
        runnables = compiled_callables[submod_name]

        piecewise_backend = PiecewiseBackend(
            graph=None,  # not needed for cached artifacts
            vllm_config=vllm_config,
            piecewise_compile_index=i,
            total_piecewise_compiles=len(piecewise_submod_names),
            sym_shape_indices=sym_shape_indices,
            vllm_backend=vllm_backend,
            returns_tuple=returns_tuple,
            compiled_runnables=runnables,
        )

        is_first = i == 0
        is_last = i == len(piecewise_submod_names) - 1
        wrapped_backend = wrap_with_cudagraph_if_needed(
            piecewise_backend,
            vllm_config,
            compilation_config,
            is_first,
            is_last,
        )

        split_gm.__dict__[submod_name] = wrapped_backend
        logger.debug(
            "Replaced submodule %s with piecewise backend from cache",
            submod_name,
        )

    # Use codegen'd execution code if available, fall back to split_gm
    execution_code = state.get("execution_code")
    submod_names = state.get("submod_names")
    if execution_code is not None and submod_names is not None:
        from vllm.compilation.codegen import compile_execution_fn

        submod_callables = {
            name: getattr(split_gm, name) for name, _ in split_gm.named_children()
        }
        runtime_callable = compile_execution_fn(
            execution_code, submod_callables, submod_names
        )
    else:
        runtime_callable = split_gm

    if compilation_config.cudagraph_copy_inputs:
        sym_tensor_indices = state["sym_tensor_indices"]
        input_buffers = [
            torch.empty_like(
                state["example_inputs"][idx], device=vllm_config.device_config.device
            )
            for idx in sym_tensor_indices
        ]
        optimized_call = make_copy_and_call(
            sym_tensor_indices, input_buffers, runtime_callable
        )
    else:
        optimized_call = runtime_callable

    fn = VllmSerializableFunction(
        **state,
        optimized_call=optimized_call,
        vllm_backend=None,
    )
    return fn