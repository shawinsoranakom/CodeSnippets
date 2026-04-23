def _validate_sample_input_elementwise_binary_sparse_mul(sample):
    # NOTE: When fixing a failing sample case, remove the
    #       corresponding if-block
    t_inp, t_args = sample.input, sample.args
    batch_dim = t_inp.dim() - t_inp.dense_dim() - t_inp.sparse_dim()
    layout = t_inp.layout
    dtype = t_inp.dtype
    if layout is torch.sparse_csr and batch_dim > 0 and t_args[0].ndim > 0:
        return ErrorInput(
            sample,
            error_regex=(
                "coo_to_sparse_csr: conversion from Sparse to SparseCsr for input"
                " tensors with sparse_dim[(][)]!=2 is not supported"
            ),
        )
    elif layout is torch.sparse_csc and t_args[0].ndim > 0:
        return ErrorInput(
            sample, error_regex="Expected result Tensor to be of format CSR"
        )
    elif layout is torch.sparse_bsr and t_args[0].ndim > 0:
        return ErrorInput(
            sample,
            error_regex="empty_sparse_compressed expected sparse compressed [(]non-block[)] tensor layout but got SparseBsr",
        )
    elif layout is torch.sparse_bsc and t_args[0].ndim > 0:
        return ErrorInput(
            sample,
            error_regex="empty_sparse_compressed expected sparse compressed [(]non-block[)] tensor layout but got SparseBsc",
        )
    elif (
        layout is torch.sparse_coo
        and dtype is torch.bool
        and t_args[0].ndim > 0
        and t_inp.is_cpu
        and t_inp.numel() > 0
        and t_inp.dense_dim() > 0
    ):
        return ErrorInput(
            sample, error_regex="\"addcmul_cpu_out\" not implemented for 'Bool'"
        )
    elif (
        layout in {torch.sparse_coo, torch.sparse_csr}
        and dtype is torch.bool
        and t_inp._nnz() > 0
        and t_args[0].ndim > 0
        and t_inp.is_cpu
        and t_inp.numel() > 0
    ):
        return ErrorInput(
            sample, error_regex="\"mul_out_sparse\" not implemented for 'Bool'"
        )
    elif (
        layout is torch.sparse_csr
        and t_args[0].layout is torch.strided
        and 0 < t_args[0].ndim
        and t_args[0].ndim < t_inp.ndim
    ):
        return ErrorInput(
            sample, error_regex="sparse_mask_sparse_csr expects self to be 2D"
        )
    elif layout is torch.sparse_csr and (
        (t_args[0].layout is torch.strided and 0 < t_args[0].ndim)
        or (t_args[0].layout is layout and t_inp.shape != t_args[0].shape)
    ):
        return ErrorInput(
            sample,
            error_regex=(
                "expects sparse inputs with equal dimensionality, number of sparse dimensions,"
                " and shape of sparse dimensions"
            ),
        )
    elif (
        layout is torch.sparse_csr
        and t_inp.dense_dim() > 0
        and t_inp._nnz() > 0
        and t_inp.is_cpu
        and dtype is torch.float16
        and t_args[0].ndim > 0
    ):
        return ErrorInput(
            sample, error_regex="\"addcmul_cpu_out\" not implemented for 'Half'"
        )
    return sample