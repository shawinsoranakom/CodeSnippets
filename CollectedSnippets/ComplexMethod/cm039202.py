def test_fetch_openml_as_frame_true(
    monkeypatch,
    data_id,
    dataset_params,
    n_samples,
    n_features,
    n_targets,
    parser,
    gzip_response,
):
    """Check the behaviour of `fetch_openml` with `as_frame=True`.

    Fetch by ID and/or name (depending if the file was previously cached).
    """
    pd = pytest.importorskip("pandas")

    _monkey_patch_webbased_functions(monkeypatch, data_id, gzip_response=gzip_response)
    bunch = fetch_openml(
        as_frame=True,
        cache=False,
        parser=parser,
        **dataset_params,
    )

    assert int(bunch.details["id"]) == data_id
    assert isinstance(bunch, Bunch)

    assert isinstance(bunch.frame, pd.DataFrame)
    assert bunch.frame.shape == (n_samples, n_features + n_targets)

    assert isinstance(bunch.data, pd.DataFrame)
    assert bunch.data.shape == (n_samples, n_features)

    if n_targets == 1:
        assert isinstance(bunch.target, pd.Series)
        assert bunch.target.shape == (n_samples,)
    else:
        assert isinstance(bunch.target, pd.DataFrame)
        assert bunch.target.shape == (n_samples, n_targets)

    assert bunch.categories is None