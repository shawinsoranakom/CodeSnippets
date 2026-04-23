def get_processor() -> VivitImageProcessor:
    extractor = VivitImageProcessor()

    assert extractor.do_resize is True
    assert extractor.size == {"shortest_edge": 256}
    assert extractor.do_center_crop is True
    assert extractor.crop_size == {"width": 224, "height": 224}
    assert extractor.resample == PILImageResampling.BILINEAR

    # here: https://github.com/deepmind/dmvr/blob/master/dmvr/modalities.py
    # one can seen that add_image has default values for normalization_mean and normalization_std set to 0 and 1
    # which effectively means no normalization (and ViViT does not overwrite those when calling this func)
    assert extractor.do_normalize is False
    assert extractor.do_rescale is True
    assert extractor.rescale_factor == 1 / 255

    # zero-centering = True in original implementation
    assert extractor.do_zero_centering is True

    return extractor