def test_correct_RandomProjection_dimensions_embedding(
    coo_container, global_random_seed
):
    data = make_sparse_random_data(
        coo_container,
        n_samples,
        n_features,
        n_nonzeros,
        random_state=global_random_seed,
        sparse_format=None,
    )
    for RandomProjection in all_RandomProjection:
        rp = RandomProjection(n_components="auto", random_state=0, eps=0.5).fit(data)

        # the number of components is adjusted from the shape of the training
        # set
        assert rp.n_components == "auto"
        assert rp.n_components_ == 110

        if RandomProjection in all_SparseRandomProjection:
            assert rp.density == "auto"
            assert_almost_equal(rp.density_, 0.03, 2)

        assert rp.components_.shape == (110, n_features)

        projected_1 = rp.transform(data)
        assert projected_1.shape == (n_samples, 110)

        # once the RP is 'fitted' the projection is always the same
        projected_2 = rp.transform(data)
        assert_array_equal(projected_1, projected_2)

        # fit transform with same random seed will lead to the same results
        rp2 = RandomProjection(random_state=0, eps=0.5)
        projected_3 = rp2.fit_transform(data)
        assert_array_equal(projected_1, projected_3)

        # Try to transform with an input X of size different from fitted.
        with pytest.raises(ValueError):
            rp.transform(data[:, 1:5])

        # it is also possible to fix the number of components and the density
        # level
        if RandomProjection in all_SparseRandomProjection:
            rp = RandomProjection(n_components=100, density=0.001, random_state=0)
            projected = rp.fit_transform(data)
            assert projected.shape == (n_samples, 100)
            assert rp.components_.shape == (100, n_features)
            assert rp.components_.nnz < 115  # close to 1% density
            assert 85 < rp.components_.nnz