def attempt_compile(
    model: torch.nn.Module,
    device: torch.device,
    imgsz: int = 640,
    use_autocast: bool = False,
    warmup: bool = False,
    mode: bool | str = "default",
) -> torch.nn.Module:
    """Compile a model with torch.compile and optionally warm up the graph to reduce first-iteration latency.

    This utility attempts to compile the provided model using the inductor backend. If compilation is unavailable or
    fails, the original model is returned unchanged. An optional warmup performs a single forward pass on a dummy input
    to prime the compiled graph and measure compile/warmup time.

    Args:
        model (torch.nn.Module): Model to compile.
        device (torch.device): Inference device used for warmup and autocast decisions.
        imgsz (int, optional): Square input size to create a dummy tensor with shape (1, 3, imgsz, imgsz) for warmup.
        use_autocast (bool, optional): Whether to run warmup under autocast on CUDA or MPS devices.
        warmup (bool, optional): Whether to execute a single dummy forward pass to warm up the compiled model.
        mode (bool | str, optional): torch.compile mode. True → "default", False → no compile, or a string like
            "default", "reduce-overhead", "max-autotune-no-cudagraphs".

    Returns:
        (torch.nn.Module): Compiled model if compilation succeeds, otherwise the original unmodified model.

    Examples:
        >>> device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        >>> # Try to compile and warm up a model with a 640x640 input
        >>> model = attempt_compile(model, device=device, imgsz=640, use_autocast=True, warmup=True)

    Notes:
        - If the current PyTorch build does not provide torch.compile, the function returns the input model immediately.
        - Warmup runs under torch.inference_mode and may use torch.autocast for CUDA/MPS to align compute precision.
        - CUDA devices are synchronized after warmup to account for asynchronous kernel execution.
    """
    if not hasattr(torch, "compile") or not mode:
        return model

    if mode is True:
        mode = "default"
    prefix = colorstr("compile:")
    LOGGER.info(f"{prefix} starting torch.compile with '{mode}' mode...")
    if mode == "max-autotune":
        LOGGER.warning(f"{prefix} mode='{mode}' not recommended, using mode='max-autotune-no-cudagraphs' instead")
        mode = "max-autotune-no-cudagraphs"
    t0 = time.perf_counter()
    try:
        model = torch.compile(model, mode=mode, backend="inductor")
    except Exception as e:
        LOGGER.warning(f"{prefix} torch.compile failed, continuing uncompiled: {e}")
        return model
    t_compile = time.perf_counter() - t0

    t_warm = 0.0
    if warmup:
        # Use a single dummy tensor to build the graph shape state and reduce first-iteration latency
        dummy = torch.zeros(1, 3, imgsz, imgsz, device=device)
        if use_autocast and device.type == "cuda":
            dummy = dummy.half()
        t1 = time.perf_counter()
        with torch.inference_mode():
            if use_autocast and device.type in {"cuda", "mps"}:
                with torch.autocast(device.type):
                    _ = model(dummy)
            else:
                _ = model(dummy)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        t_warm = time.perf_counter() - t1

    total = t_compile + t_warm
    if warmup:
        LOGGER.info(f"{prefix} complete in {total:.1f}s (compile {t_compile:.1f}s + warmup {t_warm:.1f}s)")
    else:
        LOGGER.info(f"{prefix} compile complete in {t_compile:.1f}s (no warmup)")
    return model