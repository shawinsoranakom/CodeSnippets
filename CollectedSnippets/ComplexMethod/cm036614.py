def test_multiproc_executor_multi_node():
    """
    Test MultiprocExecutor with multi-node configuration.
    This simulates 2 nodes with TP=4:
    - Node 0 (rank 0): Uses GPUs 0,1 (CUDA_VISIBLE_DEVICES=0,1) with TP=2
    - Node 1 (rank 1): Uses GPUs 2,3 (CUDA_VISIBLE_DEVICES=2,3) with TP=2
    Total world_size = 4, nnodes = 2
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]
    # symm_mem does not work for simulating multi instance in single node
    os.environ["VLLM_ALLREDUCE_USE_SYMM_MEM"] = "0"

    def run_node(node_rank: int, result_queue: multiprocessing.Queue, port: int):
        """Run a single node's executor."""
        executor = None
        try:
            # Set CUDA_VISIBLE_DEVICES for this node
            if node_rank == 0:
                os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
            else:
                os.environ["CUDA_VISIBLE_DEVICES"] = "2,3"

            # Create config for this node
            vllm_config = create_vllm_config(
                tensor_parallel_size=4,  # Total TP across all nodes
                pipeline_parallel_size=1,
                nnodes=2,  # 2 nodes
                node_rank=node_rank,
                master_port=port,  # same port
            )

            # Create executor for this node
            executor = MultiprocExecutor(vllm_config=vllm_config)

            # Verify node-specific properties
            assert executor.world_size == 4, (
                f"World size should be 4 on node {node_rank}"
            )
            assert executor.local_world_size == 2, (
                f"Local world size should be 2 on node {node_rank}"
            )
            assert len(executor.workers) == 2, (
                f"Should have 2 local workers on node {node_rank}"
            )

            # Verify worker ranks are correct for this node
            expected_ranks = [node_rank * 2, node_rank * 2 + 1]
            actual_ranks = sorted([w.rank for w in executor.workers])
            assert actual_ranks == expected_ranks, (
                f"Node {node_rank} should have workers "
                f"with ranks {expected_ranks}, got {actual_ranks}"
            )
            # Verify all workers are alive
            for worker in executor.workers:
                assert worker.proc.is_alive(), (
                    f"Worker rank {worker.rank} should be alive on node {node_rank}"
                )
            # executor.gen
            # Put success result in queue BEFORE shutdown to avoid hanging
            result_queue.put({"node": node_rank, "success": True})
            import time

            time.sleep(2)
            executor.shutdown()
        except Exception as e:
            # Put failure result in queue
            result_queue.put({"node": node_rank, "success": False, "error": str(e)})
            raise e
        finally:
            if executor is not None:
                executor.shutdown()

    # Create a queue to collect results from both processes
    result_queue: multiprocessing.Queue[dict[str, int | bool]] = multiprocessing.Queue()

    # Start both node processes
    processes = []
    for node_rank in range(2):
        p = multiprocessing.Process(
            target=run_node,
            args=(node_rank, result_queue, port),
            name=f"Node{node_rank}",
        )
        p.start()
        processes.append(p)

    # Wait for both processes to complete
    all_completed = True
    for p in processes:
        p.join(timeout=60)
        if p.is_alive():
            p.terminate()
            p.join(timeout=20)
            if p.is_alive():
                p.kill()
                p.join()
            all_completed = False

    # Check results from both nodes
    results: list[dict[str, int | bool]] = []
    while len(results) < 2:
        try:
            result = result_queue.get(timeout=1)
            results.append(result)
        except Exception:
            pass
    assert all_completed, "Not all processes completed successfully"
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert results[0]["success"], f"Node 0 failed: {results[0]}"
    assert results[1]["success"], f"Node 1 failed: {results[1]}"