def test_loader(loader_func, data_shape, target_shape, n_target, has_descr, filenames):
    bunch = loader_func()

    assert isinstance(bunch, Bunch)
    assert bunch.data.shape == data_shape
    assert bunch.target.shape == target_shape
    if hasattr(bunch, "feature_names"):
        assert len(bunch.feature_names) == data_shape[1]
    if n_target is not None:
        assert len(bunch.target_names) == n_target
    if has_descr:
        assert bunch.DESCR
    if filenames:
        assert "data_module" in bunch
        assert all(
            [
                f in bunch
                and (resources.files(bunch["data_module"]) / bunch[f]).is_file()
                for f in filenames
            ]
        )