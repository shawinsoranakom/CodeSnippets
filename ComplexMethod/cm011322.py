def run_worker(rank, world_size):
    r"""
    Initialize RPC, calls the function, and shuts down RPC.
    """
    # Using different port numbers in TCP init_method for init_rpc and
    # init_process_group to avoid port conflicts.
    rpc_backend_options = TensorPipeRpcBackendOptions()
    rpc_backend_options.init_method = "tcp://localhost:29500"

    # Rank 16. Master
    if rank == (NUM_TRAINERS + NUM_PS):
        rpc.init_rpc(
            "master",
            rank=rank,
            backend=BackendType.TENSORPIPE,  # type: ignore[attr-defined]
            world_size=world_size,
        )

        # Build the Embedding tables on the Parameter Servers.
        emb_rref_list = []
        index = 0
        while index < NUM_PS:
            ps_name = f"ps{index}"
            emb_rref = rpc.remote(
                ps_name,
                torch.nn.EmbeddingBag,
                args=(NUM_EMBEDDINGS, EMBEDDING_DIM),
                kwargs={"mode": "sum"},
            )
            emb_rref_list.append(emb_rref)
            index += 1

        # Run training loop on the trainers.
        futs = []
        for trainer_rank in range(NUM_TRAINERS):
            trainer_name = f"trainer{trainer_rank}"
            fut = rpc.rpc_async(
                trainer_name, _run_trainer, args=(emb_rref_list, trainer_rank)
            )
            futs.append(fut)

        _print_header()

        measurements_all_trainers = []
        batch_size_all_trainers = 0
        # Wait for all training to finish.
        for fut in futs:
            rank, measurements, batch_size = fut.wait()
            _print_benchmark(f"Trainer{rank}", batch_size, measurements)
            batch_size_all_trainers += batch_size
            measurements_all_trainers.append(measurements)

        _print_benchmark("All", batch_size_all_trainers, measurements_all_trainers)

    # Rank 0-7. Trainers
    elif rank >= 0 and rank < NUM_PS:
        # Initialize process group for Distributed DataParallel on trainers.
        dist.init_process_group(
            backend=dist.Backend.GLOO,
            rank=rank,
            world_size=NUM_TRAINERS,
            init_method="tcp://localhost:29501",
        )

        # Initialize RPC. Trainer just waits for RPCs from master.
        trainer_name = f"trainer{rank}"
        rpc.init_rpc(
            trainer_name,
            rank=rank,
            world_size=world_size,
            rpc_backend_options=rpc_backend_options,
        )

    # Rank 8-15. Parameter Servers
    elif rank >= NUM_TRAINERS and rank < NUM_TRAINERS + NUM_PS:
        ps_name = f"ps{rank - NUM_TRAINERS}"
        rpc.init_rpc(
            ps_name,
            rank=rank,
            world_size=world_size,
            backend=BackendType.TENSORPIPE,  # type: ignore[attr-defined]
            rpc_backend_options=rpc_backend_options,
        )
        # parameter server do nothing

    # block until all rpcs finish
    rpc.shutdown()