def _maybe_force_spawn():
    """Check if we need to force the use of the `spawn` multiprocessing start
    method.
    """
    if os.environ.get("VLLM_WORKER_MULTIPROC_METHOD") == "spawn":
        return

    reasons = []
    if is_in_ray_actor():
        # even if we choose to spawn, we need to pass the ray address
        # to the subprocess so that it knows how to connect to the ray cluster.
        # env vars are inherited by subprocesses, even if we use spawn.
        import ray

        os.environ["RAY_ADDRESS"] = ray.get_runtime_context().gcs_address
        reasons.append("In a Ray actor and can only be spawned")

    # Force spawn if NUMA binding is enabled via --numa-bind.
    # NUMA binding uses executable hijacking which requires spawn
    if "--numa-bind" in sys.argv:
        reasons.append("NUMA binding requires spawn method")

    if cuda_is_initialized():
        reasons.append("CUDA is initialized")
    elif xpu_is_initialized():
        reasons.append("XPU is initialized")

    if in_wsl():
        reasons.append("WSL is detected and NVML is not compatible with fork")

    if reasons:
        logger.warning(
            "We must use the `spawn` multiprocessing start method. "
            "Overriding VLLM_WORKER_MULTIPROC_METHOD to 'spawn'. "
            "See https://docs.vllm.ai/en/latest/usage/"
            "troubleshooting.html#python-multiprocessing "
            "for more information. Reasons: %s",
            "; ".join(reasons),
        )
        os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"