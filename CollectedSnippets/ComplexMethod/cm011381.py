def powerSGD_hook(
    state: PowerSGDState, bucket: dist.GradBucket
) -> torch.futures.Future[torch.Tensor]:
    r"""
    Implement PowerSGD algorithm.

    This DDP communication hook implements PowerSGD gradient compression
    algorithm described in the `paper <https://arxiv.org/abs/1905.13727>`_.
    Once gradient tensors are aggregated across all workers, this hook applies
    compression as follows:

    1. Views the input flattened 1D gradient tensor as a list of per-parameter tensors, and divides all the tensors into two groups:

        1.1 The tensors that should be compressed before allreduce, because the compression can give enough saving in bandwidth.

        1.2 Rest of the tensors will be directly allreduced without compression, including all the vector tensors (for biases).

    2. Handles uncompressed tensors:

        2.1. Allocate contiguous memory for those uncompressed tensors, and allreduces all the uncompressed tensors as a batch, without compression;

        2.2. Copies the individual uncompressed tensors from the contiguous memory back to the input tensor.

    3. Handles the tensors that should be compressed by PowerSGD compression:

        3.1. For each tensor M, creates two low-rank tensors P and Q for decomposing M,
        such that M = PQ^T, where Q is initialized from a standard normal distribution and orthogonalized;

        3.2. Computes each P in Ps, which is equal to MQ;

        3.3. Allreduces Ps as a batch;

        3.4. Orthogonalizes each P in Ps;

        3.5. Computes each Q in Qs, which is approximately equal to M^TP;

        3.6. Allreduces Qs as a batch;

        3.7. Computes each M among all the compressed tensors, which is approximately equal to PQ^T.

    Note that this communication hook enforces vanilla allreduce for the first ``state.start_powerSGD_iter`` iterations.
    This not only gives the user more control over the tradeoff between speedup and accuracy,
    but also helps abstract away some complexity of the internal optimization of DDP for future communication hook developers.

    Args:
        state (PowerSGDState): State information to configure the compression rate and support error feedback, warm start, etc.
            To tune the compression configs, mainly need to tune ``matrix_approximation_rank``, ``start_powerSGD_iter``
            and ``min_compression_rate``.
        bucket (dist.GradBucket): Bucket that stores a 1D flattened gradient tensor that batches multiple per-variable tensors.
            Note that since DDP comm hook only supports single process single device mode,
            only exactly one tensor is stored in this bucket.

    Returns:
        Future handler of the communication, which updates the gradients in place.

    Example::
        >>> # xdoctest: +SKIP
        >>> state = PowerSGDState(process_group=process_group, matrix_approximation_rank=1,
                                  start_powerSGD_iter=10, min_compression_rate=0.5)
        >>> ddp_model.register_comm_hook(state, powerSGD_hook)
    """
    process_group = state.process_group
    group_to_use = (
        process_group if process_group is not None else not_none(dist.group.WORLD)
    )
    world_size = group_to_use.size()

    # The input tensor is a flattened 1D tensor.
    input_tensor = bucket.buffer()

    # Run vanilla allreduce in the first `start_powerSGD_iter` iterations.
    if state.iter < state.start_powerSGD_iter:
        state.maybe_increase_iter(bucket)
        return default._allreduce_fut(group_to_use, input_tensor)

    # Apply PowerSGD after `start_powerSGD_iter` iterations.
    device = input_tensor.device
    dtype = input_tensor.dtype

    # Incorporate the error from the previous state into the gradients.
    bucket_index = bucket.index()
    input_tensor_cp = None
    total_length = input_tensor.shape[0]
    if state.use_error_feedback:
        if bucket_index in state.error_dict:
            input_tensor.add_(state.error_dict[bucket_index])
        else:
            logger.info(
                "A zero tensor of length %s that represents local error is created.",
                total_length,
            )
            state.error_dict[bucket_index] = torch.zeros(
                total_length, device=device, dtype=dtype
            )

        # Keep a copy of the input tensor,
        # so that we can compute the local error caused by compression later,
        # by comparing this copy and the input tensor updated after decompression.
        input_tensor_cp = input_tensor.detach().clone()

    # Unflatten the input tensor into per-parameter tensors, for layer-wise compression.
    tensors = bucket.gradients()

    # Step I: Divide all the tensors into two groups,
    # one will be compressed before allreduce and the other will be directly allreduced without compression.
    tensors_to_compress, uncompressed_tensors = [], []
    total_Ps_size = 0
    total_Qs_size = 0
    for tensor in tensors:
        matrix = tensor.view(tensor.shape[0], -1)
        n, m = matrix.shape
        matrix_approximation_rank = min(n, m, state.matrix_approximation_rank)
        compress_test = _should_compress(
            n, m, matrix_approximation_rank, state.min_compression_rate
        )
        state.total_numel_before_compression += compress_test[1]
        if compress_test[0]:
            tensors_to_compress.append(matrix)
            total_Ps_size += n * matrix_approximation_rank
            total_Qs_size += m * matrix_approximation_rank
            state.total_numel_after_compression += compress_test[2]
        else:
            uncompressed_tensors.append(tensor)
            state.total_numel_after_compression += compress_test[1]

    _report_compression_stats(bucket, state)

    # Step II: Handle uncompressed tensors.
    # Allocate contiguous memory for these tensors to allreduce efficiently.
    uncompressed_tensors_memory = (
        torch.cat([tensor.view(-1) for tensor in uncompressed_tensors])
        if uncompressed_tensors
        else torch.tensor([], device=device, dtype=dtype)
    )

    # Step III: Handle the tensors that should be compressed.
    # Allocate contiguous memory for Ps and Qs to allreduce efficiently.
    # If warm-start is enabled, reuse Ps and Qs from the previous iteration if possible.
    # The memory spaces of Ps and Qs need to be allocated in the first iteration when PowerSGD is applied.
    need_randomize_qs = False
    if not state.warm_start or bucket_index not in state.p_memory_dict:
        need_randomize_qs = True
        # If warm-start is disabled, low-rank tensors will be initialized at every step.
        # Only log this if warm-start to avoid spamming.
        if state.warm_start:
            logger.info(
                "Allocating contiguous memory of length %s for Ps, and of length %s for Qs, respectively.",
                total_Ps_size,
                total_Qs_size,
            )
        state.p_memory_dict[bucket_index] = torch.empty(
            total_Ps_size, device=device, dtype=dtype
        )
        state.q_memory_dict[bucket_index] = torch.empty(
            total_Qs_size, device=device, dtype=dtype
        )

    # Batch tensors to compress by shape.
    shape_to_tensors = defaultdict(list)
    for tensor in tensors_to_compress:
        shape_to_tensors[tensor.shape].append(tensor)

    # This function decides whether to batch tensors with same shape or not according to the argument,
    # so the following process could share the same code.
    def maybe_batched_tensors_to_compress():
        for tensors in shape_to_tensors.values():
            if state.batch_tensors_with_same_shape:
                batch_size = len(tensors)
                if batch_size == 1:
                    # Use the original tensor to avoid copy.
                    yield tensors[0].unsqueeze(0)
                else:
                    yield torch.stack(tensors)
            else:
                for tensor in tensors:
                    yield tensor.unsqueeze(0)

    # Create Ps and Qs that point to the allocated memory.
    tensors_to_compress = []
    ps = []
    qs = []
    p_idx = 0
    q_idx = 0
    for tensor in maybe_batched_tensors_to_compress():
        batch_size, n, m = tensor.shape
        matrix_approximation_rank = min(n, m, state.matrix_approximation_rank)
        tensors_to_compress.append(tensor)
        ps.append(
            state.p_memory_dict[bucket_index][
                p_idx : p_idx + batch_size * n * matrix_approximation_rank
            ].view(batch_size, n, matrix_approximation_rank)
        )
        qs.append(
            state.q_memory_dict[bucket_index][
                q_idx : q_idx + batch_size * m * matrix_approximation_rank
            ].view(batch_size, m, matrix_approximation_rank)
        )
        p_idx += batch_size * n * matrix_approximation_rank
        q_idx += batch_size * m * matrix_approximation_rank

    # If warm-start is enabled, reuse Qs from the previous iteration if possible and skip filling random values.
    # The exception is the first iteration when PowerSGD is applied.
    if not need_randomize_qs:
        for q in qs:
            _orthogonalize(q, state.orthogonalization_epsilon)
    else:
        with torch.random.fork_rng(devices=[]):
            # Fork this RNG to avoid changing the seed globally and affecting the random sampling anywhere else in the training.
            # The seed makes sure that the initial random values are the same across all the DDP replicas.
            # This seed should differ at every step.
            # Since it is very slow to fork RNG state across all the CUDA devices,
            # only fork on CPU and then move the generated tensor to the CUDA device (by overwriting q).
            torch.manual_seed(state.rng.randint(1_000_000_000))
            for q in qs:
                q.copy_(
                    torch.randn(
                        *q.shape,
                        device="cpu",
                        dtype=dtype,
                    )
                )
                _orthogonalize(q, state.orthogonalization_epsilon)

    # Compute Ps.
    for tensor, q, p in zip(tensors_to_compress, qs, ps):
        torch.bmm(tensor, q, out=p)

    # This allreduce is only applied to uncompressed tensors,
    # so it should have been kicked off before the above computation on the compressed tensors to hide more communication costs.
    # However, this somehow requires a separate future chain at this time.
    allreduce_contiguous_uncompressed_tensors_fut = dist.all_reduce(
        uncompressed_tensors_memory, group=group_to_use, async_op=True
    ).get_future()

    def unpack_uncompressed_tensors_and_allreduce_ps(fut):
        uncompressed_tensors_memory = fut.value()[0].div_(world_size)
        idx = 0
        for tensor in uncompressed_tensors:
            tensor.copy_(
                uncompressed_tensors_memory[idx : idx + tensor.numel()].view_as(tensor)
            )
            idx += tensor.numel()

        # Since these Ps will be orthogonalized later, no need to divide them by world size.
        return (
            dist.all_reduce(
                state.p_memory_dict[bucket_index], group=group_to_use, async_op=True
            )
            .get_future()
            .wait()[0]
        )

    def compute_qs(fut):
        state.p_memory_dict[bucket_index] = fut.value()
        for p in ps:
            _orthogonalize(p, state.orthogonalization_epsilon)

        # Compute Qs.
        for tensor, p, q in zip(tensors_to_compress, ps, qs):
            torch.bmm(tensor.transpose(1, 2), p, out=q)

        # TODO: The above procedure does two matmul+allreduce steps per iteration --
        # one left multiplication and one right multiplication.
        # For warm-start, can take one such step at a time, and alternate between them.

        # Allreduce Qs.
        return (
            dist.all_reduce(
                state.q_memory_dict[bucket_index], group=group_to_use, async_op=True
            )
            .get_future()
            .wait()[0]
        )

    def decompress(fut):
        state.q_memory_dict[bucket_index] = fut.value().div_(world_size)

        for p, q, tensor in zip(ps, qs, tensors_to_compress):
            torch.bmm(p, q.transpose(1, 2), out=tensor)

        # Copy batched tensors back to original buffer.
        if state.batch_tensors_with_same_shape:
            for tensor in tensors_to_compress:
                if tensor.shape[0] == 1:
                    # Skip tensor with batch_size == 1 since itself is the original tensor.
                    continue
                original_tensors = shape_to_tensors[tensor.shape[1:]]
                for i, original_tensor in enumerate(original_tensors):
                    original_tensor.copy_(tensor[i])

        if torch.cuda.is_available():
            torch.cuda.synchronize(device)

        if state.use_error_feedback:
            # Memorize the local errors.
            if input_tensor_cp is None:
                raise AssertionError
            state.error_dict[bucket_index] = input_tensor_cp - input_tensor
        if not state.warm_start:
            state.p_memory_dict.clear()
            state.q_memory_dict.clear()

        state.maybe_increase_iter(bucket)

        return input_tensor

    return (
        allreduce_contiguous_uncompressed_tensors_fut.then(
            unpack_uncompressed_tensors_and_allreduce_ps
        )
        .then(compute_qs)
        .then(decompress)
    )