def run_triton_kernel_with_autotune(
    pending_kernels: dict[str, Any],
    kernel_name: str,
    stream: Any,
    args: list[Any],
) -> TritonKernelCompileResult:
    """
    Run a Triton kernel with full autotuning using actual tensor arguments.
    """
    from torch._inductor.codecache import CodeCacheFuture, CudaKernelParamCache
    from torch._inductor.runtime.triton_heuristics import config_to_dict

    if kernel_name not in pending_kernels:
        raise RuntimeError(f"Kernel {kernel_name} not found in pending kernels.")
    kernel_obj = pending_kernels[kernel_name]

    if isinstance(kernel_obj, CodeCacheFuture):
        kernel_fn = kernel_obj.result()
    elif isinstance(kernel_obj, CachingAutotuner):
        kernel_fn = kernel_obj
    else:
        raise RuntimeError(f"Unexpected kernel object type: {type(kernel_obj)}")

    assert isinstance(kernel_fn, CachingAutotuner)

    inductor_meta = kernel_fn.inductor_meta
    inductor_meta["store_cubin"] = True

    # For TMA kernels, wrap tensor args with TMA descriptors
    args = _wrap_tma_args(args, kernel_fn)

    # Run the kernel with the provided arguments
    # This will trigger autotuning if there are multiple configs
    kernel_fn.run(*args, stream=stream)
    if not kernel_fn.launchers:
        raise RuntimeError("Kernel run did not produce any launchers")
    launcher = kernel_fn.launchers[0]

    cached_params: dict[str, Any] | None = CudaKernelParamCache.get(kernel_name)
    if cached_params is None:
        raise RuntimeError(f"Failed to get cached params for kernel {kernel_name}")

    from torch._inductor.codecache import get_cpp_wrapper_cubin_path_name

    cubin_path_name = get_cpp_wrapper_cubin_path_name()
    for key_name in (cubin_path_name, "mangled_name", "num_warps", "shared_mem"):
        if key_name not in cached_params:
            raise RuntimeError(
                f"{key_name} not found in cached params for {kernel_name}"
            )
    cubin_path = cached_params[cubin_path_name]
    mangled_name = cached_params["mangled_name"]
    num_warps = cached_params["num_warps"]
    shared_mem = cached_params["shared_mem"]

    config = config_to_dict(launcher.config) if launcher.config else {}

    # For combo/foreach kernels, the autotuned config may have empty kwargs
    # (e.g., the foreach heuristic only tunes num_warps, not XBLOCK).
    # In that case, use the default_config from combo_grid_meta
    combo_grid_meta = inductor_meta.get("combo_grid_meta") if inductor_meta else None
    default_config = combo_grid_meta.get("default_config") if combo_grid_meta else None
    if default_config:
        config = {**default_config, **config}

    xblock = config.get("XBLOCK", 128)
    yblock = config.get("YBLOCK", 1)
    zblock = config.get("ZBLOCK", 1)
    r0block = config.get("R0_BLOCK", 1)
    rsplit = config.get("RSPLIT", 1)
    rsplit_size = config.get("RSPLIT_SIZE", 1)

    config_index = None
    grid_type = inductor_meta.get("grid_type") if inductor_meta else None
    if grid_type == "PrecomputedGrid" and inductor_meta:
        # PrecomputedGrid selects one of precomputed_grids. We use config_index
        # to remember which grid is chosen.
        precomputed_grids = inductor_meta.get("precomputed_grids", [])
        for idx, entry in enumerate(precomputed_grids):
            entry_config = entry.get("config", {})
            if all(config.get(k) == v for k, v in entry_config.items()):
                config_index = idx
                break

    global_scratch: int | None = cached_params.get("global_scratch")
    profile_scratch: int | None = cached_params.get("profile_scratch")

    log.debug(
        "Successfully autotuned Triton kernel: cubin_path=%s, mangled_name=%s, "
        "num_warps=%d, shared_mem=%d, xblock=%d, yblock=%d, zblock=%d, r0block=%d, "
        "rsplit=%d, rsplit_size=%d, config_index=%s, global_scratch=%s, profile_scratch=%s",
        cubin_path,
        mangled_name,
        num_warps,
        shared_mem,
        xblock,
        yblock,
        zblock,
        r0block,
        rsplit,
        rsplit_size,
        config_index,
        global_scratch,
        profile_scratch,
    )

    result = TritonKernelCompileResult(
        cubin_path=cubin_path,
        mangled_name=mangled_name,
        num_warps=num_warps,
        shared_mem=shared_mem,
        xblock=xblock,
        yblock=yblock,
        zblock=zblock,
        r0block=r0block,
        rsplit=rsplit,
        rsplit_size=rsplit_size,
        config_index=config_index,
        global_scratch=global_scratch,
        profile_scratch=profile_scratch,
    )
    return result