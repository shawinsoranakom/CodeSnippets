def test_constants_get_color(config: dict[str, T.Any],
                             patch_config,  # noqa[F811]
                             mocker: pytest_mock.MockerFixture) -> None:
    """ Test ConstantsAugmentation._get_color works as expected """
    patch_config(cfg.Augmentation, config)
    clahe_mock = mocker.patch(f"{MODULE_PREFIX}.ConstantsAugmentation._get_clahe",
                              return_value=(1, 2.0, 3))
    lab_mock = mocker.patch(f"{MODULE_PREFIX}.ConstantsAugmentation._get_lab",
                            return_value=np.array([1.0, 2.0, 3.0], dtype="float32"))
    color = ConstantsAugmentation._get_color(256)
    clahe_mock.assert_called_once_with(256)
    lab_mock.assert_called_once_with()
    assert isinstance(color, ConstantsColor)
    assert isinstance(color.clahe_base_contrast, int)
    assert isinstance(color.clahe_chance, float)
    assert isinstance(color.clahe_max_size, int)
    assert isinstance(color.lab_adjust, np.ndarray)

    assert color.clahe_base_contrast == clahe_mock.return_value[0]
    assert color.clahe_chance == clahe_mock.return_value[1]
    assert color.clahe_max_size == clahe_mock.return_value[2]
    assert np.all(color.lab_adjust == lab_mock.return_value)