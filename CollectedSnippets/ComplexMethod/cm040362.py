def sparse_wrapper(x1, x2):
            if isinstance(x1, jax_sparse.JAXSparse):
                if isinstance(x2, jax_sparse.JAXSparse):
                    # x1 and x2 are sparse.
                    # The way we use `sparsify` it cannot know that the indices
                    # are the same, so we optimize this case here.
                    if (
                        x1.indices is x2.indices
                        and isinstance(x1, jax_sparse.BCOO)
                        and isinstance(x2, jax_sparse.BCOO)
                    ):
                        if not linear and not x1.unique_indices:
                            x1 = jax_sparse.bcoo_sum_duplicates(x1)
                            x2 = jax_sparse.bcoo_sum_duplicates(x2)
                        return jax_sparse.BCOO(
                            (func(x1.data, x2.data), x1.indices),
                            shape=x1.shape,
                            indices_sorted=x1.indices_sorted,
                            unique_indices=x1.unique_indices,
                        )
                    elif use_sparsify:
                        return sparse_func(x1, x2)
                    elif isinstance(x1, jax_sparse.BCOO) and isinstance(
                        x2, jax_sparse.BCOO
                    ):
                        x1 = bcoo_add_indices(x1, x2, sum_duplicates=not linear)
                        x2 = bcoo_add_indices(x2, x1, sum_duplicates=not linear)
                        return jax_sparse.BCOO(
                            (func(x1.data, x2.data), x1.indices),
                            shape=x1.shape,
                            indices_sorted=True,
                            unique_indices=True,
                        )
                    else:
                        ValueError(
                            "Unsupported sparse format: "
                            f"{x1.__class__} and {x2.__class__}"
                        )
                else:
                    # x1 is sparse, x2 is dense, densify x2.
                    x1 = x1.todense()
            elif isinstance(x2, jax_sparse.JAXSparse):
                # x1 is dense, x2 is sparse, densify x2.
                x2 = x2.todense()
            return func(x1, x2)