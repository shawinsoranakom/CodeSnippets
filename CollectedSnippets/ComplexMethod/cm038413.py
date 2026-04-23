def ensure_model_parallel_initialized(
    tensor_model_parallel_size: int,
    pipeline_model_parallel_size: int,
    prefill_context_model_parallel_size: int = 1,
    decode_context_model_parallel_size: int | None = 1,
    backend: str | None = None,
) -> None:
    """Helper to initialize model parallel groups if they are not initialized,
    or ensure tensor-parallel and pipeline-parallel sizes are equal to expected
    values if the model parallel groups are initialized.
    """
    world_group = get_world_group()
    if hasattr(world_group, "backend"):
        backend = backend or world_group.backend
    else:
        backend = backend or torch.distributed.get_backend(world_group.device_group)
    if not model_parallel_is_initialized():
        initialize_model_parallel(
            tensor_model_parallel_size,
            pipeline_model_parallel_size,
            prefill_context_model_parallel_size,
            decode_context_model_parallel_size,
            backend,
        )
        return

    assert get_tensor_model_parallel_world_size() == tensor_model_parallel_size, (
        "tensor parallel group already initialized, but of unexpected size. "
        f"got: {get_tensor_model_parallel_world_size()=} vs. "
        f"wanted: {tensor_model_parallel_size=}"
    )
    pp_world_size = get_pp_group().world_size
    assert pp_world_size == pipeline_model_parallel_size, (
        "pipeline parallel group already initialized, but of unexpected size. "
        f"got: {pp_world_size=} vs. "
        f"wanted: {pipeline_model_parallel_size=}"
    )
    pcp_world_size = get_pcp_group().world_size
    assert pcp_world_size == prefill_context_model_parallel_size, (
        "prefill context parallel group already initialized, but of unexpected size: "
        f"{pcp_world_size=} vs. "
        f"{prefill_context_model_parallel_size=}"
    )