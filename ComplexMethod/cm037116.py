def monitor_torch_compile(
    vllm_config: VllmConfig,
    message: str = "torch.compile took %.2f s in total",
    is_encoder: bool = False,
) -> Generator[None, None, None]:
    """Context manager that times torch.compile and manages depyf debugging.

    On normal exit: logs the compile time and exits depyf.
    On exception: cleans up depyf without logging (compilation failed).
    """
    global torch_compile_start_time
    torch_compile_start_time = time.perf_counter()

    compilation_config = vllm_config.compilation_config
    depyf_cm = None
    path = vllm_config.compile_debug_dump_path()
    if compilation_config.mode == CompilationMode.VLLM_COMPILE and path:
        import depyf

        path.mkdir(parents=True, exist_ok=True)
        logger.debug("Dumping depyf output to %s", path)
        depyf_cm = depyf.prepare_debug(path.as_posix())
        depyf_cm.__enter__()

    try:
        yield
    except Exception:
        raise
    else:
        total_compile_time = time.perf_counter() - torch_compile_start_time
        if compilation_config.mode == CompilationMode.VLLM_COMPILE:
            if is_encoder:
                compilation_config.encoder_compilation_time += total_compile_time
            else:
                compilation_config.compilation_time += total_compile_time
            logger.info_once(message, total_compile_time)
    finally:
        if depyf_cm is not None:
            try:
                depyf_cm.__exit__(None, None, None)
            except Exception:
                logger.warning("Exception during depyf cleanup.", exc_info=True)