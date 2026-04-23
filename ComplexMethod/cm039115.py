def test_maxabs_scaler_partial_fit(csr_container):
    # Test if partial_fit run over many batches of size 1 and 50
    # gives the same results as fit
    X = X_2d[:100, :]
    n = X.shape[0]

    for chunk_size in [1, 2, 50, n, n + 42]:
        # Test mean at the end of the process
        scaler_batch = MaxAbsScaler().fit(X)

        scaler_incr = MaxAbsScaler()
        scaler_incr_csr = MaxAbsScaler()
        scaler_incr_csc = MaxAbsScaler()
        for batch in gen_batches(n, chunk_size):
            scaler_incr = scaler_incr.partial_fit(X[batch])
            X_csr = csr_container(X[batch])
            scaler_incr_csr = scaler_incr_csr.partial_fit(X_csr)
            X_csc = csr_container(X[batch])
            scaler_incr_csc = scaler_incr_csc.partial_fit(X_csc)

        assert_array_almost_equal(scaler_batch.max_abs_, scaler_incr.max_abs_)
        assert_array_almost_equal(scaler_batch.max_abs_, scaler_incr_csr.max_abs_)
        assert_array_almost_equal(scaler_batch.max_abs_, scaler_incr_csc.max_abs_)
        assert scaler_batch.n_samples_seen_ == scaler_incr.n_samples_seen_
        assert scaler_batch.n_samples_seen_ == scaler_incr_csr.n_samples_seen_
        assert scaler_batch.n_samples_seen_ == scaler_incr_csc.n_samples_seen_
        assert_array_almost_equal(scaler_batch.scale_, scaler_incr.scale_)
        assert_array_almost_equal(scaler_batch.scale_, scaler_incr_csr.scale_)
        assert_array_almost_equal(scaler_batch.scale_, scaler_incr_csc.scale_)
        assert_array_almost_equal(scaler_batch.transform(X), scaler_incr.transform(X))

        # Test std after 1 step
        batch0 = slice(0, chunk_size)
        scaler_batch = MaxAbsScaler().fit(X[batch0])
        scaler_incr = MaxAbsScaler().partial_fit(X[batch0])

        assert_array_almost_equal(scaler_batch.max_abs_, scaler_incr.max_abs_)
        assert scaler_batch.n_samples_seen_ == scaler_incr.n_samples_seen_
        assert_array_almost_equal(scaler_batch.scale_, scaler_incr.scale_)
        assert_array_almost_equal(scaler_batch.transform(X), scaler_incr.transform(X))

        # Test std until the end of partial fits, and
        scaler_batch = MaxAbsScaler().fit(X)
        scaler_incr = MaxAbsScaler()  # Clean estimator
        for i, batch in enumerate(gen_batches(n, chunk_size)):
            scaler_incr = scaler_incr.partial_fit(X[batch])
            assert_correct_incr(
                i,
                batch_start=batch.start,
                batch_stop=batch.stop,
                n=n,
                chunk_size=chunk_size,
                n_samples_seen=scaler_incr.n_samples_seen_,
            )