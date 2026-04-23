def test_concurrent_senders_single_receiver():
    """Test N concurrent senders sharing one queue with a single receiver.

    Each sender encodes multiple messages (each containing two tensors) via
    its own MsgpackEncoder + TensorIpcSender.  A single TensorIpcReceiver
    on the receiving side must correctly drain-and-buffer interleaved
    TensorIpcData items from the shared queue and match them back to the
    right message handles during decode.
    """
    num_senders = 4
    num_messages_per_sender = 3
    tensor_queue = torch_mp.Queue()
    payload_queue: mp.Queue = mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    barrier = mp.Barrier(num_senders)
    retrieval_done = mp.Event()

    # Launch sender processes
    processes = []
    for i in range(num_senders):
        proc = mp.Process(
            target=concurrent_sender_process,
            args=(
                tensor_queue,
                payload_queue,
                result_queue,
                i,
                num_messages_per_sender,
                barrier,
                retrieval_done,
            ),
        )
        proc.start()
        processes.append(proc)

    # Collect send confirmations
    send_results = []
    for _ in range(num_senders):
        send_results.append(result_queue.get(timeout=15.0))
    for r in send_results:
        assert r["success"], (
            f"Sender {r['sender_index']} failed: {r.get('error')}\n"
            f"{r.get('traceback', '')}"
        )

    # Now decode all messages from the main process using a single receiver
    receiver = TensorIpcReceiver(tensor_queue)
    decoder = MsgpackDecoder(MultiTensorMessage, oob_tensor_provider=receiver)

    decoded_messages: list[MultiTensorMessage] = []
    total = num_senders * num_messages_per_sender
    for _ in range(total):
        encoded = payload_queue.get(timeout=10.0)
        decoded = decoder.decode(encoded)
        assert isinstance(decoded, MultiTensorMessage)
        decoded_messages.append(decoded)

    # Signal senders they can exit
    retrieval_done.set()

    # Group by sender_label prefix to verify all messages arrived
    by_sender: dict[int, list[MultiTensorMessage]] = {}
    for msg in decoded_messages:
        # label format: "sender_{i}_msg_{j}"
        parts = msg.sender_label.split("_")
        sender_idx = int(parts[1])
        by_sender.setdefault(sender_idx, []).append(msg)

    assert len(by_sender) == num_senders, (
        f"Expected {num_senders} senders, got {len(by_sender)}"
    )

    for sender_idx in range(num_senders):
        msgs = sorted(by_sender[sender_idx], key=lambda m: m.sender_label)
        assert len(msgs) == num_messages_per_sender, (
            f"Sender {sender_idx}: expected {num_messages_per_sender} "
            f"messages, got {len(msgs)}"
        )
        for msg_idx, msg in enumerate(msgs):
            assert msg.sender_label == f"sender_{sender_idx}_msg_{msg_idx}"
            # Verify tensor shapes match what the sender created
            assert msg.t1.shape == (sender_idx + 1, 3)
            assert msg.t2.shape == (2, sender_idx + 2)
            # Verify tensor values
            assert torch.allclose(msg.t1, torch.full_like(msg.t1, float(msg_idx)))
            assert torch.allclose(msg.t2, torch.full_like(msg.t2, float(msg_idx + 100)))

    for proc in processes:
        proc.join(timeout=5.0)