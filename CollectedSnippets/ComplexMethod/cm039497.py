def _euclidean_distances_upcast(X, XX=None, Y=None, YY=None, batch_size=None):
    """Euclidean distances between X and Y.

    Assumes X and Y have float32 dtype.
    Assumes XX and YY have float64 dtype or are None.

    X and Y are upcast to float64 by chunks, which size is chosen to limit
    memory increase by approximately 10% (at least 10MiB).
    """
    xp, _, device_ = get_namespace_and_device(X, Y)
    n_samples_X = X.shape[0]
    n_samples_Y = Y.shape[0]
    n_features = X.shape[1]

    distances = xp.empty((n_samples_X, n_samples_Y), dtype=xp.float32, device=device_)

    if batch_size is None:
        x_density = X.nnz / np.prod(X.shape) if issparse(X) else 1
        y_density = Y.nnz / np.prod(Y.shape) if issparse(Y) else 1

        # Allow 10% more memory than X, Y and the distance matrix take (at
        # least 10MiB)
        maxmem = max(
            (
                (x_density * n_samples_X + y_density * n_samples_Y) * n_features
                + (x_density * n_samples_X * y_density * n_samples_Y)
            )
            / 10,
            10 * 2**17,
        )

        # The increase amount of memory in 8-byte blocks is:
        # - x_density * batch_size * n_features (copy of chunk of X)
        # - y_density * batch_size * n_features (copy of chunk of Y)
        # - batch_size * batch_size (chunk of distance matrix)
        # Hence x² + (xd+yd)kx = M, where x=batch_size, k=n_features, M=maxmem
        #                                 xd=x_density and yd=y_density
        tmp = (x_density + y_density) * n_features
        batch_size = (-tmp + math.sqrt(tmp**2 + 4 * maxmem)) / 2
        batch_size = max(int(batch_size), 1)

    x_batches = gen_batches(n_samples_X, batch_size)
    xp_max_float = _max_precision_float_dtype(xp=xp, device=device_)
    for i, x_slice in enumerate(x_batches):
        X_chunk = xp.astype(X[x_slice, :], xp_max_float)
        if XX is None:
            XX_chunk = row_norms(X_chunk, squared=True)[:, None]
        else:
            XX_chunk = XX[x_slice]

        y_batches = gen_batches(n_samples_Y, batch_size)

        for j, y_slice in enumerate(y_batches):
            if X is Y and j < i:
                # when X is Y the distance matrix is symmetric so we only need
                # to compute half of it.
                d = distances[y_slice, x_slice].T

            else:
                Y_chunk = xp.astype(Y[y_slice, :], xp_max_float)
                if YY is None:
                    YY_chunk = row_norms(Y_chunk, squared=True)[None, :]
                else:
                    YY_chunk = YY[:, y_slice]

                d = -2 * safe_sparse_dot(X_chunk, Y_chunk.T, dense_output=True)
                d += XX_chunk
                d += YY_chunk

            distances[x_slice, y_slice] = xp.astype(d, xp.float32, copy=False)

    return distances