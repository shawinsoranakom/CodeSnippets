def bincount(x, weights=None, minlength=0, sparse=False):
    # Note: bincount is never traceable / jittable because the output shape
    # depends on the values in x.
    if sparse or isinstance(x, jax_sparse.BCOO):
        if isinstance(x, jax_sparse.BCOO):
            if weights is not None:
                if not isinstance(weights, jax_sparse.BCOO):
                    raise ValueError("`x` and `weights` must both be BCOOs")
                if x.indices is not weights.indices:
                    # This test works in eager mode only
                    if not jnp.all(jnp.equal(x.indices, weights.indices)):
                        raise ValueError(
                            "`x` and `weights` BCOOs must have the same indices"
                        )
                weights = weights.data
            x = x.data
        reduction_axis = 1 if len(x.shape) > 1 else 0
        maxlength = jnp.maximum(jnp.max(x) + 1, minlength)
        one_hot_encoding = nn.one_hot(x, maxlength, sparse=True)
        if weights is not None:
            expanded_weights = jnp.expand_dims(weights, reduction_axis + 1)
            one_hot_encoding = one_hot_encoding * expanded_weights

        outputs = jax_sparse.bcoo_reduce_sum(
            one_hot_encoding,
            axes=(reduction_axis,),
        )
        return outputs
    if len(x.shape) == 2:
        if weights is None:

            def bincount_fn(arr):
                return jnp.bincount(arr, minlength=minlength)

            bincounts = list(map(bincount_fn, x))
        else:

            def bincount_fn(arr_w):
                return jnp.bincount(
                    arr_w[0], weights=arr_w[1], minlength=minlength
                )

            bincounts = list(map(bincount_fn, zip(x, weights)))

        return jnp.stack(bincounts)
    return jnp.bincount(x, weights=weights, minlength=minlength)