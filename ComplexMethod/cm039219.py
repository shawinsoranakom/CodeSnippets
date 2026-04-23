def test_dump(csr_container):
    X_sparse, y_dense = _load_svmlight_local_test_file(datafile)
    X_dense = X_sparse.toarray()
    y_sparse = csr_container(np.atleast_2d(y_dense))

    # slicing a csr_matrix can unsort its .indices, so test that we sort
    # those correctly
    X_sliced = X_sparse[np.arange(X_sparse.shape[0])]
    y_sliced = y_sparse[np.arange(y_sparse.shape[0])]

    for X in (X_sparse, X_dense, X_sliced):
        for y in (y_sparse, y_dense, y_sliced):
            for zero_based in (True, False):
                for dtype in [np.float32, np.float64, np.int32, np.int64]:
                    f = BytesIO()
                    # we need to pass a comment to get the version info in;
                    # LibSVM doesn't grok comments so they're not put in by
                    # default anymore.

                    if sp.issparse(y) and y.shape[0] == 1:
                        # make sure y's shape is: (n_samples, n_labels)
                        # when it is sparse
                        y = y.T

                    # Note: with dtype=np.int32 we are performing unsafe casts,
                    # where X.astype(dtype) overflows. The result is
                    # then platform dependent and X_dense.astype(dtype) may be
                    # different from X_sparse.astype(dtype).asarray().
                    X_input = X.astype(dtype)

                    dump_svmlight_file(
                        X_input, y, f, comment="test", zero_based=zero_based
                    )
                    f.seek(0)

                    comment = f.readline()
                    comment = str(comment, "utf-8")

                    assert "scikit-learn %s" % sklearn.__version__ in comment

                    comment = f.readline()
                    comment = str(comment, "utf-8")

                    assert ["one", "zero"][zero_based] + "-based" in comment

                    X2, y2 = load_svmlight_file(f, dtype=dtype, zero_based=zero_based)
                    assert X2.dtype == dtype
                    assert_array_equal(X2.sorted_indices().indices, X2.indices)

                    X2_dense = X2.toarray()
                    if sp.issparse(X_input):
                        X_input_dense = X_input.toarray()
                    else:
                        X_input_dense = X_input

                    if dtype == np.float32:
                        # allow a rounding error at the last decimal place
                        assert_array_almost_equal(X_input_dense, X2_dense, 4)
                        assert_array_almost_equal(
                            y_dense.astype(dtype, copy=False), y2, 4
                        )
                    else:
                        # allow a rounding error at the last decimal place
                        assert_array_almost_equal(X_input_dense, X2_dense, 15)
                        assert_array_almost_equal(
                            y_dense.astype(dtype, copy=False), y2, 15
                        )