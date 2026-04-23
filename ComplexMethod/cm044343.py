def test_constants_get_transform(config: dict[str, T.Any],
                                 size: int,
                                 patch_config) -> None:  # noqa[F811]
    """ Test ConstantsAugmentation._get_transform works as expected """
    patch_config(cfg.Augmentation, config)
    transform = ConstantsAugmentation._get_transform(size)
    assert isinstance(transform, ConstantsTransform)
    assert isinstance(transform.rotation, int)
    assert isinstance(transform.zoom, float)
    assert isinstance(transform.shift, float)
    assert isinstance(transform.flip, float)
    assert transform.rotation == config["rotation_range"]
    assert transform.zoom == config["zoom_amount"] / 100.
    assert transform.shift == (config["shift_range"] / 100.) * size
    assert transform.flip == config["flip_chance"] / 100.