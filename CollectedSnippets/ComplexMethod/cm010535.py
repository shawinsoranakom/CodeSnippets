def _densify(x):
    # return a copy of sparse x with all unspecified elements
    # "replaced" with zero-valued elements
    if isinstance(x, (list, tuple)):
        return type(x)(map(_densify, x))
    elif not is_tensor_like(x) or x.layout in {torch.strided, torch._mkldnn}:  # type: ignore[attr-defined] # no attr _mkldnn
        return x
    elif x.layout is torch.sparse_coo:
        device = x.device
        indices_dtype = x._indices().dtype
        tmp = torch.ones(x.shape[: x.sparse_dim()], dtype=torch.int8, device=device)
        indices = tmp.nonzero().t().to(dtype=indices_dtype)
        values = torch.zeros(
            (tmp.numel(), *x.shape[x.sparse_dim() :]), dtype=x.dtype, device=device
        )
        x_coalesced = x.detach().coalesce()
        if x_coalesced.numel() > 0:
            stride = tmp.stride()
            flat_indices = (
                x_coalesced.indices()
                .mul(
                    torch.tensor(stride, dtype=indices_dtype, device=device).unsqueeze(
                        1
                    )
                )
                .sum(0)
            )
            values[flat_indices] = x_coalesced.values()
        return (
            torch.sparse_coo_tensor(indices, values, x.shape)
            ._coalesced_(True)
            .requires_grad_(x.requires_grad)
        )
    elif _is_sparse_compressed_tensor(x):
        blocksize = (
            x.values().shape[1:3]
            if x.layout in {torch.sparse_bsr, torch.sparse_bsc}
            else None
        )
        compressed_indices = (
            x.crow_indices()
            if x.layout in {torch.sparse_csr, torch.sparse_bsr}
            else x.ccol_indices()
        )
        # We'll use intermediate sparse COO for simplicity
        r = _densify(x.detach().to_sparse(layout=torch.sparse_coo)).to_sparse(
            layout=x.layout, blocksize=blocksize
        )
        # Check that all elements are specified also after `to_sparse` op:
        dense_numel = r.values().numel() // max(1, r.values().shape[0])
        batch_numel = compressed_indices.numel() // compressed_indices.shape[-1]
        sparse_numel = r.numel() // max(1, dense_numel * batch_numel)
        if sparse_numel != r._nnz():
            raise AssertionError(
                f"{x.layout} densify failed: expected nnz={sparse_numel} but got {r._nnz()}"
            )
        return r.requires_grad_(x.requires_grad)
    elif _is_sparse_any_tensor(x):
        raise NotImplementedError(x.layout)
    return x