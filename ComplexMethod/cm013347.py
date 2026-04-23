def _maybe_failing_sample_inputs_sparse_elementwise_binary_mul(
    op_info, device, dtype, requires_grad, layout, **kwargs
):
    """Generator of samples that are known to fail or that were failing in past."""
    # NOTE: When fixing a failing case, remove the Exception comment
    #       but keep the `yield sample` statement.

    blocksize = (1, 1) if layout in {torch.sparse_bsr, torch.sparse_bsc} else None
    regular = torch.tensor([[1, 2], [3, 4]], device=device, dtype=dtype).to_sparse(
        layout=layout, dense_dim=0, blocksize=blocksize
    )
    batch = torch.tensor(
        [[[1, 2], [3, 4]], [[4, 5], [6, 7]]], device=device, dtype=dtype
    ).to_sparse(layout=layout, dense_dim=0, blocksize=blocksize)
    hybrid = torch.tensor(
        [[[1], [2]], [[3], [4]]], device=device, dtype=dtype
    ).to_sparse(layout=layout, dense_dim=1, blocksize=blocksize)

    if layout is torch.sparse_csr:
        # RuntimeError: crow_indices is supposed to be a vector, but got 2 dimensional tensor
        yield SampleInput(batch, args=(batch,))
        # RuntimeError: Only tensors with two sparse dimensions can be
        # converted to the SparseCsr layout, got self with 3 sparse
        # dimensions.
        yield SampleInput(
            torch.zeros_like(hybrid).requires_grad_(requires_grad),
            args=(torch.zeros_like(hybrid).requires_grad_(requires_grad),),
        )
        if dtype is torch.complex32:
            # RuntimeError: "mul_out_sparse" not implemented for 'ComplexHalf'
            yield SampleInput(regular, args=(regular,))
        if dtype is torch.bool and regular.is_cpu:
            # RuntimeError: "mul_out_sparse" not implemented for 'Bool'
            yield SampleInput(regular, args=(regular,))
    if layout is torch.sparse_csc:
        # RuntimeError: Expected result Tensor to be of format CSR
        yield SampleInput(regular, args=(regular,))
    if layout is torch.sparse_bsr:
        # RuntimeError: empty_sparse_compressed expected sparse compressed (non-block) tensor layout but got SparseBsr
        yield SampleInput(regular, args=(regular,))
    if layout is torch.sparse_bsc:
        # RuntimeError: empty_sparse_compressed expected sparse compressed (non-block) tensor layout but got SparseBsc
        yield SampleInput(regular, args=(regular,))
    if layout is torch.sparse_coo:
        if dtype is torch.complex32:
            # RuntimeError: "mul_out_sparse" not implemented for 'ComplexHalf'
            yield SampleInput(regular, args=(regular,))
        if dtype is torch.bool and regular.is_cpu:
            # RuntimeError: "mul_out_sparse" not implemented for 'Bool'
            yield SampleInput(regular, args=(regular,))
        if dtype in {torch.bool, torch.float16} and regular.is_cpu:
            # RuntimeError: "addcmul_cpu_out" not implemented for '(Bool|Half)'
            yield SampleInput(hybrid, args=(hybrid,))