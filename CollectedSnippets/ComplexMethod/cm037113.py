def reset_compile_wrapper(model: torch.nn.Module) -> None:
    """
    Clean up compiled model and captured CUDA graphs for elastic EP.
    """
    if not isinstance(model, TorchCompileWithNoGuardsWrapper) and hasattr(
        model, "model"
    ):
        model = model.model
    if not isinstance(model, TorchCompileWithNoGuardsWrapper):
        return
    # model.do_not_compile is set by the @support_torch_compile decorator
    if hasattr(model, "do_not_compile") and model.do_not_compile:
        return
    from vllm.compilation.counter import compilation_counter

    # reset the compilation counter
    compilation_counter.num_models_seen = 0
    compilation_counter.num_graphs_seen = 0
    compilation_counter.num_piecewise_graphs_seen = 0
    compilation_counter.num_piecewise_capturable_graphs_seen = 0
    compilation_counter.num_backend_compilations = 0
    compilation_counter.num_gpu_runner_capture_triggers = 0
    compilation_counter.num_cudagraph_captured = 0
    compilation_counter.num_inductor_compiles = 0
    compilation_counter.num_eager_compiles = 0
    compilation_counter.num_cache_entries_updated = 0
    compilation_counter.num_compiled_artifacts_saved = 0
    compilation_counter.stock_torch_compile_count = 0
    compilation_counter.num_aot_compiles = 0
    compilation_counter.num_aot_artifacts_saved = 0
    compilation_counter.num_aot_artifacts_loaded = 0

    # Clear the AOT compiled function so the model is forced to
    # recompile on the next call. Without this, decorators.py
    # __call__ uses the stale aot_compiled_fn whose torchinductor
    # kernels have old parameters (expert_map size for example)
    # baked in as compile-time constants.
    if hasattr(model, "aot_compiled_fn"):
        model.aot_compiled_fn = None
    if hasattr(model, "was_aot_compile_fn_loaded_from_disk"):
        model.was_aot_compile_fn_loaded_from_disk = False

    # Reset the cache_dir so VllmBackend recomputes the hash
    # (data_parallel_size changed, so the config hash differs).
    compilation_config = model.vllm_config.compilation_config
    compilation_config.cache_dir = ""
    compilation_config.local_cache_dir = ""

    model.__class__.forward.__code__ = model.original_code_object()
    TorchCompileWithNoGuardsWrapper.__init__(
        model,
        compile_prefix=model._compile_prefix,
        is_encoder=model._is_encoder,
    )