def test_20news_vectorized(fetch_20newsgroups_vectorized_fxt):
    # test subset = train
    bunch = fetch_20newsgroups_vectorized_fxt(subset="train")
    assert sp.issparse(bunch.data) and bunch.data.format == "csr"
    assert bunch.data.shape == (11314, 130107)
    assert bunch.target.shape[0] == 11314
    assert bunch.data.dtype == np.float64
    assert bunch.DESCR.startswith(".. _20newsgroups_dataset:")

    # test subset = test
    bunch = fetch_20newsgroups_vectorized_fxt(subset="test")
    assert sp.issparse(bunch.data) and bunch.data.format == "csr"
    assert bunch.data.shape == (7532, 130107)
    assert bunch.target.shape[0] == 7532
    assert bunch.data.dtype == np.float64
    assert bunch.DESCR.startswith(".. _20newsgroups_dataset:")

    # test return_X_y option
    fetch_func = partial(fetch_20newsgroups_vectorized_fxt, subset="test")
    check_return_X_y(bunch, fetch_func)

    # test subset = all
    bunch = fetch_20newsgroups_vectorized_fxt(subset="all")
    assert sp.issparse(bunch.data) and bunch.data.format == "csr"
    assert bunch.data.shape == (11314 + 7532, 130107)
    assert bunch.target.shape[0] == 11314 + 7532
    assert bunch.data.dtype == np.float64
    assert bunch.DESCR.startswith(".. _20newsgroups_dataset:")