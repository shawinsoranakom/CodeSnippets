def _aot_stage2c_make_autograd_function(
    aot_config: AOTConfig,
    flat_args: list[Any],
    fw_metadata: ViewAndMutationMeta,
    maybe_subclass_meta: SubclassMeta | None,
    wrappers: list[CompilerWrapper],
    compiled_fw_func: Callable[..., Any],
    compiled_bw_func: Callable[..., Any] | None,
    lazy_backward_info: AutogradLazyBackwardCompileInfo | None,
    try_save_cache_entry: Callable[..., Any],
    entry: GenericAOTAutogradResult[Any, Any] | None,
    _indices_of_inps_to_detach: list[int],
    num_symints_saved_for_bw: int,
) -> DispatchReturn:
    backward_state_indices = [
        idx for idx, x in enumerate(flat_args) if isinstance(x, BackwardState)
    ]
    if len(backward_state_indices) > 1:
        raise AssertionError(
            f"expected at most 1 backward_state_index, got {len(backward_state_indices)}"
        )

    disable_amp = torch._C._is_any_autocast_enabled()
    compile_spec = AOTDispatchAutogradCompileSpec(
        compiled_fw_func=compiled_fw_func,
        compiled_bw_func=compiled_bw_func,
        maybe_subclass_meta=maybe_subclass_meta,
        num_symints_saved_for_bw=num_symints_saved_for_bw,
        backward_state_indices=backward_state_indices,
        disable_amp=disable_amp,
        indices_of_inps_to_detach=_indices_of_inps_to_detach,
        lazy_backward_info=lazy_backward_info,
        aot_config=aot_config,
        fw_metadata=fw_metadata,
        try_save_cache_entry=try_save_cache_entry,
    )
    compiled_fn = AOTDispatchAutograd.post_compile(compile_spec)

    if entry is not None:
        compiled_fn = SerializableCompiledFunction(compiled_fn, lambda: entry)

    if config.debug_assert:
        flat_requires_grad: list[bool | None] = [
            a.requires_grad if isinstance(a, Tensor) else None for a in flat_args
        ]
        compiled_fn = DebugAssertWrapper(
            flat_requires_grad=flat_requires_grad
        ).post_compile(compiled_fn, aot_config, runtime_metadata=fw_metadata)

    compiled_fn = post_compile(
        wrappers,
        compiled_fn,
        aot_config,
        runtime_metadata=fw_metadata,
    )
    return compiled_fn