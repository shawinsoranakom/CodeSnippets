def enable_ray_v2_backend():
    """Set env vars for the Ray V2 executor backend and shut down Ray
    between tests."""
    import ray

    saved = {
        "VLLM_USE_RAY_V2_EXECUTOR_BACKEND": os.environ.get(
            "VLLM_USE_RAY_V2_EXECUTOR_BACKEND"
        ),
        "VLLM_ENABLE_V1_MULTIPROCESSING": os.environ.get(
            "VLLM_ENABLE_V1_MULTIPROCESSING"
        ),
    }
    os.environ["VLLM_USE_RAY_V2_EXECUTOR_BACKEND"] = "1"
    os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"
    if ray.is_initialized():
        ray.shutdown()
    try:
        yield
    finally:
        if ray.is_initialized():
            ray.shutdown()
        os.environ.update({k: v for k, v in saved.items() if v is not None})
        for key in (k for k, v in saved.items() if v is None):
            os.environ.pop(key, None)