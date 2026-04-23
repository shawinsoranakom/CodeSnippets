def test_multiple_senders_single_receiver_ipc():
    """Test N senders sharing a queue with a single receiver via msgpack.

    Simulates the real vLLM topology where multiple API server frontends
    each have their own MsgpackEncoder + TensorIpcSender, all putting
    tensors onto the same torch.mp queue, and a single engine core
    decodes them with one MsgpackDecoder + TensorIpcReceiver.
    """
    import torch.multiprocessing as torch_mp

    from vllm.v1.engine.tensor_ipc import TensorIpcReceiver, TensorIpcSender

    num_senders = 3
    num_messages_per_sender = 2
    tensor_queue = torch_mp.Queue()

    # Create N independent senders (each gets its own uuid-based sender_id)
    senders = []
    encoders = []
    for _ in range(num_senders):
        s = TensorIpcSender(tensor_queue)
        senders.append(s)
        encoders.append(MsgpackEncoder(oob_tensor_consumer=s))

    # Single receiver
    receiver = TensorIpcReceiver(tensor_queue)
    decoder = MsgpackDecoder(RequestWithTensor, oob_tensor_provider=receiver)

    # Encode messages from all senders, interleaving the order
    # so that tensors from different senders land on the queue interleaved.
    encoded_payloads: list[tuple[int, int, torch.Tensor, list]] = []
    for msg_idx in range(num_messages_per_sender):
        for sender_idx in range(num_senders):
            tensor = torch.full(
                (sender_idx + 1, msg_idx + 2),
                float(sender_idx * 100 + msg_idx),
                dtype=torch.float32,
            )
            req = RequestWithTensor(
                prompt_embeds=tensor,
                data=f"s{sender_idx}_m{msg_idx}",
            )
            encoded = encoders[sender_idx].encode(req)
            encoded_payloads.append((sender_idx, msg_idx, tensor, encoded))

    # Decode all messages — the receiver must correctly match each
    # tensor handle to the right TensorIpcData from the shared queue.
    for sender_idx, msg_idx, original_tensor, encoded in encoded_payloads:
        decoded = decoder.decode(encoded)
        assert isinstance(decoded, RequestWithTensor)
        assert decoded.data == f"s{sender_idx}_m{msg_idx}"
        assert decoded.prompt_embeds is not None
        assert decoded.prompt_embeds.shape == original_tensor.shape, (
            f"Shape mismatch for sender {sender_idx} msg {msg_idx}: "
            f"{decoded.prompt_embeds.shape} != {original_tensor.shape}"
        )
        assert torch.allclose(decoded.prompt_embeds, original_tensor), (
            f"Value mismatch for sender {sender_idx} msg {msg_idx}"
        )