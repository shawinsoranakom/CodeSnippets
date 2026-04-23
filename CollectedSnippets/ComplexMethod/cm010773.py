def _chunked_standard_basis_for_(
    tensors: Sequence[torch.Tensor],
    tensor_numels: Sequence[int],
    chunk_size: int | None = None,
) -> Generator[tuple[torch.Tensor, ...], None, None]:
    # This function:
    # - constructs a N=sum(tensor_numels) standard basis. i.e. an NxN identity matrix.
    # - Splits the identity matrix into chunks with each chunk size determined by `tensor_numels`.
    # - Each chunk corresponds to one tensor. The chunk has the same dtype and
    #   device as the tensor
    #
    # For example, with tensor_numels = [1, 2, 1], this function returns:
    # ( tensor([[1],     tensor([[0, 0],      tensor([[0],
    #           [0],             [1, 0],              [0],
    #           [0],             [0, 1],              [0],
    #           [0]])  ,         [0, 0]])  ,          [1]])  )
    #
    # Precondition: tensor_numels == tuple(tensor.numel() for tensor in tensors)
    # Precondition: tensors always has at least one element.
    #
    # See NOTE: [Computing jacobian with vmap and grad for multiple tensors]
    # for context behind this function.
    # NOTE: Argument `chunk_size` is used to generate chunked basis instead of
    #       one huge basis matrix. `chunk_size` dictates the maximum size of the
    #       basis matrix along dim=0.
    if len(tensors) != len(tensor_numels):
        raise AssertionError(
            f"len(tensors)={len(tensors)} != len(tensor_numels)={len(tensor_numels)}"
        )
    if len(tensors) == 0:
        raise AssertionError("tensors must have at least one element")
    if chunk_size is not None and chunk_size <= 0:
        raise AssertionError(f"chunk_size must be > 0 or None, got {chunk_size}")
    total_numel = sum(tensor_numels)
    if chunk_size and chunk_size < total_numel:
        chunk_numels = get_chunk_sizes(total_numel, chunk_size)
    else:  # chunk_size is None or chunk_size >= total_numel
        chunk_size = total_numel
        chunk_numels = [total_numel]

    diag_start_indices = (
        0,
        *torch.tensor(tensor_numels).cumsum(dim=0)[:-1].neg().unbind(),
    )

    for chunk_idx, total_numel in enumerate(chunk_numels):
        chunks = tuple(
            tensor.new_zeros(total_numel, tensor_numel)
            for tensor, tensor_numel in zip(tensors, tensor_numels)
        )

        for chunk, diag_start_idx in zip(chunks, diag_start_indices):
            offset = int(diag_start_idx) + chunk_idx * chunk_size
            chunk.diagonal(offset).fill_(1)
        chunks = tuple(
            chunk.view(total_numel, *tensor.shape)
            for chunk, tensor in zip(chunks, tensors)
        )
        yield chunks