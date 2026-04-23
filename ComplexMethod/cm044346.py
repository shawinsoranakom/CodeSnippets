def test_image_augmentation_init(size: int,
                                 batch_size: int,
                                 patch_config) -> None:  # noqa[F811]
    """ Test ImageAugmentation initializes """
    patch_config(cfg.Augmentation, _CONFIG)
    attrs = {"_processing_size": int,
             "_batch_size": int,
             "_constants": ConstantsAugmentation}
    instance = get_instance(batch_size, size)

    assert all(x in instance.__dict__ for x in attrs)
    assert all(x in attrs for x in instance.__dict__)
    assert isinstance(instance._batch_size, int)
    assert isinstance(instance._processing_size, int)
    assert isinstance(instance._constants, ConstantsAugmentation)
    assert instance._batch_size == batch_size
    assert instance._processing_size == size