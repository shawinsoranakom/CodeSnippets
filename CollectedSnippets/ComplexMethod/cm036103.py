def test_multiple_api_servers_to_engine():
    """Test multiple API servers sending to one engine core via multiprocessing."""
    num_api_servers = 3
    tensor_queue = torch_mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    barrier = mp.Barrier(num_api_servers)
    retrieval_done = mp.Event()

    # Start multiple API server processes
    processes = []
    for server_id in range(num_api_servers):
        proc = mp.Process(
            target=api_server_worker,
            args=(server_id, tensor_queue, result_queue, barrier, retrieval_done),
        )
        proc.start()
        processes.append(proc)

    # Collect results from all servers
    results = []
    for _ in range(num_api_servers):
        result = result_queue.get(timeout=10.0)
        results.append(result)

    # Verify all servers succeeded
    for result in results:
        assert result["success"], (
            f"Server {result['server_id']} failed: {result.get('error')}"
        )

    # Verify all tensors are in queue
    received_tensors = []
    for _ in range(num_api_servers):
        ipc_data = tensor_queue.get(timeout=1.0)
        received_tensors.append((ipc_data.sender_id, ipc_data.tensor))

    assert len(received_tensors) == num_api_servers

    # Verify tensor content (order may vary with multiprocessing)
    tensor_by_sender = {sid: t for sid, t in received_tensors}
    for server_id in range(num_api_servers):
        expected_id = f"server_{server_id}"
        assert expected_id in tensor_by_sender, (
            f"Missing tensor from server {server_id}"
        )
        expected_tensor = torch.ones(server_id + 1, server_id + 2) * server_id
        assert torch.allclose(tensor_by_sender[expected_id], expected_tensor)

    # Signal workers that retrieval is complete
    retrieval_done.set()

    # Wait for all processes to complete
    for proc in processes:
        proc.join(timeout=5.0)