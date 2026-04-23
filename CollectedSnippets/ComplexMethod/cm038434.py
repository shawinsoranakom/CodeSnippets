def packed_broadcast_producer(
    iterator: Iterator[tuple[str, torch.Tensor]],
    group: Any,
    src: int,
    post_iter_func: Callable[[tuple[str, torch.Tensor]], torch.Tensor],
    buffer_size_bytes: int = DEFAULT_PACKED_BUFFER_SIZE_BYTES,
    num_buffers: int = DEFAULT_PACKED_NUM_BUFFERS,
) -> None:
    """Broadcast tensors in a packed manner from trainer to workers.

    Args:
        iterator: Iterator of model parameters. Returns a tuple of (name, tensor)
        group: Process group (PyNcclCommunicator)
        src: Source rank (0 in current implementation)
        post_iter_func: Function to apply to each (name, tensor) pair before
                       packing, should return a tensor
        buffer_size_bytes: Size in bytes for each packed tensor buffer.
                          Both producer and consumer must use the same value.
        num_buffers: Number of buffers for double/triple buffering.
                    Both producer and consumer must use the same value.

    """
    target_packed_tensor_size = buffer_size_bytes

    streams = [torch.cuda.Stream() for _ in range(num_buffers)]
    buffer_idx = 0

    packing_tensor_list: list[list[torch.Tensor]] = [[] for _ in range(num_buffers)]
    packing_tensor_sizes: list[int] = [0 for _ in range(num_buffers)]
    packed_tensors: list[torch.Tensor] = [
        torch.empty(0, dtype=torch.uint8, device="cuda") for _ in range(num_buffers)
    ]

    while True:
        # Synchronize the current stream
        streams[buffer_idx].synchronize()
        # Start tasks for the new buffer in a new stream
        with torch.cuda.stream(streams[buffer_idx]):
            try:
                # Initialize the packing tensor list and sizes
                packing_tensor_list[buffer_idx] = []
                packing_tensor_sizes[buffer_idx] = 0
                # Pack the tensors
                while True:
                    # Apply post processing and convert to linearized uint8 tensor
                    tensor = (
                        post_iter_func(next(iterator))
                        .contiguous()
                        .view(torch.uint8)
                        .view(-1)
                    )
                    packing_tensor_list[buffer_idx].append(tensor)
                    packing_tensor_sizes[buffer_idx] += tensor.numel()
                    if packing_tensor_sizes[buffer_idx] > target_packed_tensor_size:
                        break
                # Pack the tensors and call broadcast collective
                packed_tensors[buffer_idx] = torch.cat(
                    packing_tensor_list[buffer_idx], dim=0
                )
                group.broadcast(packed_tensors[buffer_idx], src=src)
                # Move to the next buffer
                buffer_idx = (buffer_idx + 1) % num_buffers
            except StopIteration:
                # Do the last broadcast if there are remaining tensors
                if len(packing_tensor_list[buffer_idx]) > 0:
                    packed_tensors[buffer_idx] = torch.cat(
                        packing_tensor_list[buffer_idx], dim=0
                    )
                    group.broadcast(packed_tensors[buffer_idx], src=src)
                break