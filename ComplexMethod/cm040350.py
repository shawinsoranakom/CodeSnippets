def matmul(x1, x2):
    x1 = convert_to_tensor(x1)
    x2 = convert_to_tensor(x2)
    # When both x1 and x2 are of int8, specifying `preferred_element_type` as
    # int32 to enable hardware-accelerated matmul
    x1_dtype = standardize_dtype(x1.dtype)
    x2_dtype = standardize_dtype(x2.dtype)
    if x1_dtype == "int8" and x2_dtype == "int8":
        preferred_element_type = "int32"
    else:
        preferred_element_type = None
    if isinstance(x1, jax_sparse.JAXSparse) or isinstance(
        x2, jax_sparse.JAXSparse
    ):
        if not hasattr(matmul, "sparse_matmul"):
            matmul.sparse_matmul = jax_sparse.sparsify(jnp.matmul)
        if isinstance(x1, jax_sparse.BCOO):
            x1 = jax_sparse.bcoo_update_layout(
                x1, n_batch=len(x1.shape) - 2, on_inefficient="warn"
            )
        if isinstance(x2, jax_sparse.BCOO):
            x2 = jax_sparse.bcoo_update_layout(
                x2, n_batch=len(x2.shape) - 2, on_inefficient="warn"
            )
        return matmul.sparse_matmul(
            x1, x2, preferred_element_type=preferred_element_type
        )

    return jnp.matmul(x1, x2, preferred_element_type=preferred_element_type)