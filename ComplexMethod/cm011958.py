def get_cpp_wrapper_config(log_cudagraph_skip: bool = True) -> dict[str, object]:
    if log_cudagraph_skip and config.triton.cudagraphs and config.graph_partition:
        log_cudagraph_skip_and_bump_counter(
            format_default_skip_message(
                "cpp-wrapper does not support graph partition yet"
            )
        )

    autotune_at_compile_time = (
        config.triton.autotune_at_compile_time
        if config.triton.autotune_at_compile_time is not None
        # Default to True for AOTI. Subject to change in future.
        else has_triton() and V.aot_compilation
    )
    return {
        "triton.autotune_at_compile_time": autotune_at_compile_time,
        "triton.autotune_cublasLt": not autotune_at_compile_time,
        "triton.cudagraphs": (
            config.triton.cudagraphs
            and not V.aot_compilation
            and not config.graph_partition
        ),
        "triton.store_cubin": True,
    }