def sample_inputs_sparse_reduction(
    op_info, device, dtype, requires_grad, layout, blocksize=None, **kwargs
):
    """Sample inputs for reduction operations on sparse tensors."""
    layout_name = str(layout).split(".", 1)[-1].rsplit("_coo", 1)[0]
    op_supports_layout = getattr(op_info, "supports_" + layout_name)
    if not op_supports_layout:
        return

    for sample_input in sample_inputs_reduction(
        op_info, device, dtype, requires_grad, **kwargs
    ):
        if sample_input.input.ndim == 0:
            # scalar sparse tensors are not supported
            continue

        if layout in {
            torch.sparse_csr,
            torch.sparse_csc,
            torch.sparse_bsr,
            torch.sparse_bsc,
        }:
            if sample_input.input.ndim < 2:
                # conversion to sparse compressed tensors requires at
                # least 2 dimensional tensors
                continue
            if sample_input.input.ndim > 2 and (sample_input.input == 0).any():
                # Skip batched sparse compressed samples that contain
                # explicit zeros because to_sparse(layout=..) will
                # fail, see gh-98495.
                # TODO: remove this if-block after gh-98495 is fixed.
                continue

        if layout in {torch.sparse_bsr, torch.sparse_bsc} and blocksize is None:
            blocksize = (1, 1)

        yield SampleInput(
            sample_input.input.detach()
            .to_sparse(layout=layout, blocksize=blocksize)
            .requires_grad_(requires_grad),
            args=sample_input.args,
            kwargs=sample_input.kwargs,
        )

        if layout is torch.sparse_coo and (dtype.is_floating_point or dtype.is_complex):
            # uncoalesced samples
            inp = sample_input.input.detach().to_sparse(layout=layout)
            inp = torch.sparse_coo_tensor(
                inp.indices().repeat(1, 2),
                inp.values().repeat(2),
                inp.shape,
                dtype=inp.dtype,
                device=inp.device,
            )
            if inp.is_coalesced():
                raise AssertionError("Expected inp to not be coalesced")
            yield SampleInput(
                inp.requires_grad_(requires_grad),
                args=sample_input.args,
                kwargs=sample_input.kwargs,
            )

        if sample_input.input.ndim > 2:
            # hybrid samples
            yield SampleInput(
                sample_input.input.detach()
                .to_sparse(
                    layout=layout,
                    blocksize=blocksize,
                    dense_dim=sample_input.input.ndim - 2,
                )
                .requires_grad_(requires_grad),
                args=sample_input.args,
                kwargs=sample_input.kwargs,
            )