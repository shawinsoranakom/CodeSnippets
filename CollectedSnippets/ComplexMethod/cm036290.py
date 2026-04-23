def test_init_distributed_is_called_before_memory_snapshot():
    """Test that distributed env is setup before memory snapshot.

    This test makes sure during worker initialization, the initial memory
    snapshot is taken after distributed env is setup to include all the buffers
    allocated by distributed env.
    """
    world_size = 2

    # Create a temporary file for distributed init
    with tempfile.NamedTemporaryFile(delete=False) as f:
        distributed_init_method = f"file://{f.name}"

    # Create queues for inter-process communication
    ctx = mp.get_context("spawn")
    operation_queue = ctx.Queue()
    error_queue = ctx.Queue()

    # Start worker processes
    processes = []
    for rank in range(world_size):
        p = ctx.Process(
            target=worker_process,
            args=(
                rank,
                world_size,
                distributed_init_method,
                operation_queue,
                error_queue,
            ),
        )
        p.start()
        processes.append(p)

    # Wait for all processes to complete
    for p in processes:
        p.join(timeout=60)  # 60 second timeout

    # Check for errors
    errors = []
    while not error_queue.empty():
        rank, error_msg, error_type = error_queue.get()
        errors.append(f"Rank {rank}: {error_type}: {error_msg}")

    if errors:
        pytest.fail("Worker processes failed:\n" + "\n".join(errors))

    # Collect all operations from the queue
    operations = []
    while not operation_queue.empty():
        operations.append(operation_queue.get())

    # Verify we got operations from both ranks
    print(f"Collected operations: {operations}")

    # Check operations for each rank
    for rank in range(world_size):
        rank_ops = [op for op, r in operations if r == rank]
        print(f"\nRank {rank} operations: {rank_ops}")

        # Raises ValueError if the operation is not found
        init_distributed = rank_ops.index("init_distributed")
        nccl_all_reduce = rank_ops.index("nccl_all_reduce")
        memory_snapshot = rank_ops.index("memory_snapshot")

        # Verify order: init_distributed should happen before memory_snapshot
        assert init_distributed < nccl_all_reduce < memory_snapshot, (
            f"Rank {rank}: init_distributed (index {init_distributed}) "
            f"must happen before nccl_all_reduce (index {nccl_all_reduce}) "
            f"and memory_snapshot (index {memory_snapshot})"
        )

    # Clean up
    os.unlink(distributed_init_method.replace("file://", ""))