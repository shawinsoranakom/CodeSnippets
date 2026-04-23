def test_standard_scaler_partial_fit():
    # Test if partial_fit run over many batches of size 1 and 50
    # gives the same results as fit
    X = X_2d
    n = X.shape[0]

    for chunk_size in [1, 2, 50, n, n + 42]:
        # Test mean at the end of the process
        scaler_batch = StandardScaler(with_std=False).fit(X)

        scaler_incr = StandardScaler(with_std=False)
        for batch in gen_batches(n_samples, chunk_size):
            scaler_incr = scaler_incr.partial_fit(X[batch])
        assert_array_almost_equal(scaler_batch.mean_, scaler_incr.mean_)
        assert scaler_batch.var_ == scaler_incr.var_  # Nones
        assert scaler_batch.n_samples_seen_ == scaler_incr.n_samples_seen_

        # Test std after 1 step
        batch0 = slice(0, chunk_size)
        scaler_incr = StandardScaler().partial_fit(X[batch0])
        if chunk_size == 1:
            assert_array_almost_equal(
                np.zeros(n_features, dtype=np.float64), scaler_incr.var_
            )
            assert_array_almost_equal(
                np.ones(n_features, dtype=np.float64), scaler_incr.scale_
            )
        else:
            assert_array_almost_equal(np.var(X[batch0], axis=0), scaler_incr.var_)
            assert_array_almost_equal(
                np.std(X[batch0], axis=0), scaler_incr.scale_
            )  # no constants

        # Test std until the end of partial fits, and
        scaler_batch = StandardScaler().fit(X)
        scaler_incr = StandardScaler()  # Clean estimator
        for i, batch in enumerate(gen_batches(n_samples, chunk_size)):
            scaler_incr = scaler_incr.partial_fit(X[batch])
            assert_correct_incr(
                i,
                batch_start=batch.start,
                batch_stop=batch.stop,
                n=n,
                chunk_size=chunk_size,
                n_samples_seen=scaler_incr.n_samples_seen_,
            )

        assert_array_almost_equal(scaler_batch.var_, scaler_incr.var_)
        assert scaler_batch.n_samples_seen_ == scaler_incr.n_samples_seen_