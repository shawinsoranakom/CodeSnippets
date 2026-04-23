def test_concurrent_senders_interleaved_buffer():
    """Test receiver buffering when tensors from multiple senders interleave.

    Manually enqueue TensorIpcData from two senders in an interleaved order
    and verify the receiver correctly buffers and retrieves each tensor by
    its (sender_id, message_id, tensor_id) handle.
    """
    tensor_queue = torch_mp.Queue()

    # Sender A: 2 tensors for message 1
    a_t0 = torch.randn(2, 3)
    a_t1 = torch.randn(4, 5)
    # Sender B: 2 tensors for message 1
    b_t0 = torch.randn(6, 7)
    b_t1 = torch.randn(8, 9)

    # Interleave: B_t0, A_t0, B_t1, A_t1
    for sid, mid, tid, t in [
        ("B", 1, 0, b_t0),
        ("A", 1, 0, a_t0),
        ("B", 1, 1, b_t1),
        ("A", 1, 1, a_t1),
    ]:
        tensor_queue.put(
            TensorIpcData(sender_id=sid, message_id=mid, tensor_id=tid, tensor=t)
        )

    receiver = TensorIpcReceiver(tensor_queue)

    # Request A_t1 first — receiver must drain and buffer B_t0, A_t0, B_t1
    result = receiver(
        "float32", a_t1.shape, {"sender_id": "A", "message_id": 1, "tensor_id": 1}
    )
    assert torch.equal(result, a_t1)

    # Now request B_t0 from buffer
    result = receiver(
        "float32", b_t0.shape, {"sender_id": "B", "message_id": 1, "tensor_id": 0}
    )
    assert torch.equal(result, b_t0)

    # Request A_t0 from buffer
    result = receiver(
        "float32", a_t0.shape, {"sender_id": "A", "message_id": 1, "tensor_id": 0}
    )
    assert torch.equal(result, a_t0)

    # Request B_t1 from buffer
    result = receiver(
        "float64", b_t1.shape, {"sender_id": "B", "message_id": 1, "tensor_id": 1}
    )
    assert torch.equal(result, b_t1)

    # All buffers should be drained
    for sid in ("A", "B"):
        tensors = receiver._tensor_buffers[sid].tensors.get(1, {})
        assert len(tensors) == 0, f"Sender {sid} buffer not empty: {tensors}"