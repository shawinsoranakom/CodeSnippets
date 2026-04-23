def torch_distributed_zero_first(local_rank: int):
    """Ensure all processes in distributed training wait for the local master (rank 0) to complete a task first."""
    initialized = dist.is_available() and dist.is_initialized()
    use_ids = initialized and dist.get_backend() == "nccl"

    if initialized and local_rank not in {-1, 0}:
        dist.barrier(device_ids=[local_rank]) if use_ids else dist.barrier()
    yield
    if initialized and local_rank == 0:
        dist.barrier(device_ids=[local_rank]) if use_ids else dist.barrier()