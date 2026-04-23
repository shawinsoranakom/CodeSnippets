def test_fetch_openml_as_frame_false(
    monkeypatch,
    data_id,
    dataset_params,
    n_samples,
    n_features,
    n_targets,
    parser,
):
    """Check the behaviour of `fetch_openml` with `as_frame=False`.

    Fetch both by ID and/or name + version.
    """
    pytest.importorskip("pandas")

    _monkey_patch_webbased_functions(monkeypatch, data_id, gzip_response=True)
    bunch = fetch_openml(
        as_frame=False,
        cache=False,
        parser=parser,
        **dataset_params,
    )
    assert int(bunch.details["id"]) == data_id
    assert isinstance(bunch, Bunch)

    assert bunch.frame is None

    assert isinstance(bunch.data, np.ndarray)
    assert bunch.data.shape == (n_samples, n_features)

    assert isinstance(bunch.target, np.ndarray)
    if n_targets == 1:
        assert bunch.target.shape == (n_samples,)
    else:
        assert bunch.target.shape == (n_samples, n_targets)

    assert isinstance(bunch.categories, dict)