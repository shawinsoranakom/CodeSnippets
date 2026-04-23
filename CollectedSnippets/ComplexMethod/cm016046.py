def load_dlmc_dataset(
    dataset_path,
    operation,
    hidden_size,
    sparsity,
    device,
    requires_grad,
    n_limit=math.inf,
):
    """load_dlmc_dataset loads a DLMC dataset for a matmul performance test.
    Args:
        dataset_path:
            path of the dataset from DLMC collection.
        operation:
            This value allows tensors for `sparse@sparse`|`sparse@dense`|`sparse@vector` operations.
        hidden_size
            This value allows tensors of varying sizes.
        sparsity:
            This value allows tensors of varying sparsities.
        device:
            Whether to place the Tensor on a GPU or CPU.
        requires_grad:
            Loads the dataset for backward test.
        n_limit:
            This value allows a dataset with some limit size.
    """
    if operation == "sparse@sparse" or operation == "sparse@dense":
        collection = load_spmm_dataset(
            dataset_path, hidden_size, sparsity, operation, device, n_limit
        )
    elif operation == "sparse@vector":
        collection = load_spmv_dataset(
            dataset_path, hidden_size, sparsity, device, n_limit
        )
    scipy_vars = {}
    backward_vars = {}
    for x, y in collection:
        if device == "cpu":
            scipy_vars = {
                "sx": to_coo_scipy(x) if x.is_sparse else x.numpy(),
                "sy": to_coo_scipy(y) if y.is_sparse else y.numpy(),
            }
        if not requires_grad:
            dx = x.to_dense() if x.is_sparse else x
            dy = y.to_dense() if y.is_sparse else y
        else:
            c = sparse_grad_output(x, y)
            backward_vars = {
                "sparse_grad_output": c,
                "grad_output": c.to_dense() if c.is_sparse else c,
            }
            x.requires_grad_(True)
            y.requires_grad_(True)
            dx = x.to_dense().detach() if x.is_sparse else x.clone().detach()
            dy = y.to_dense().detach() if y.is_sparse else y.clone().detach()
            dx.requires_grad_(True)
            dy.requires_grad_(True)
        yield {"x": x, "y": y, "dx": dx, "dy": dy, **scipy_vars, **backward_vars}