def sparse_wrapper(x1, x2):
        if isinstance(x1, jax_sparse.JAXSparse):
            if isinstance(x2, jax_sparse.JAXSparse):
                # x1 is sparse and x2 is sparse.
                # Divisor is sparse, meaning we're doing divisions by zero
                # outside of x2.indices, so the result is dense. Densify both.
                x1 = x1.todense()
                x2 = x2.todense()
            elif isinstance(x1, jax_sparse.BCOO):
                if not hasattr(x2, "shape") or len(x2.shape) == 0:
                    # x1 is sparse BCOO, x2 is scalar, apply func element-wise.
                    return jax_sparse.BCOO(
                        (func(x1.data, x2), x1.indices),
                        shape=x1.shape,
                        indices_sorted=x1.indices_sorted,
                        unique_indices=x1.unique_indices,
                    )
                else:
                    # x1 is sparse BCOO, x2 is dense.
                    if not jax_utils.is_in_jax_tracing_scope(x2):
                        # Find zeros and nans in x2 and add indices to x1.
                        # 1. Create a dense mask for zeros and nans.
                        x2_zeros_and_nans = jnp.equal(x2, 0)
                        if not jnp.issubdtype(x2.dtype, jnp.integer):
                            x2_zeros_and_nans = jnp.logical_or(
                                x2_zeros_and_nans, jnp.isnan(x2)
                            )
                        # 2. Make it a BCOO of True values.
                        x2_zeros_and_nans = jax_sparse.bcoo_fromdense(
                            x2_zeros_and_nans,
                            n_batch=x1.n_batch,
                            n_dense=x1.n_dense,
                            index_dtype=x1.indices.dtype,
                        )
                        # 3. Add the indices to x1.
                        x1 = bcoo_add_indices(
                            x1, x2_zeros_and_nans, sum_duplicates=True
                        )
                    return sparse_func(x1, x2)
            else:
                raise ValueError(f"Unsupported sparse format: {x1.__class__}")
        elif isinstance(x2, jax_sparse.JAXSparse):
            # x1 is dense, x2 is sparse, densify x2
            x2 = x2.todense()
        return func(x1, x2)