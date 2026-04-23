def convert_feature_extractor(feature_extractor, tiny_config):
    to_convert = False
    kwargs = {}
    if hasattr(tiny_config, "image_size"):
        kwargs["size"] = tiny_config.image_size
        kwargs["crop_size"] = tiny_config.image_size
        to_convert = True
    elif (
        hasattr(tiny_config, "vision_config")
        and tiny_config.vision_config is not None
        and hasattr(tiny_config.vision_config, "image_size")
    ):
        kwargs["size"] = tiny_config.vision_config.image_size
        kwargs["crop_size"] = tiny_config.vision_config.image_size
        to_convert = True

    # Speech2TextModel specific.
    if hasattr(tiny_config, "input_feat_per_channel"):
        kwargs["feature_size"] = tiny_config.input_feat_per_channel
        kwargs["num_mel_bins"] = tiny_config.input_feat_per_channel
        to_convert = True

    if to_convert:
        feature_extractor = feature_extractor.__class__(**kwargs)

    # Sanity check: on tiny image feature extractors, a large image size results in slow CI -- up to the point where it
    # can result in timeout issues.
    if (
        isinstance(feature_extractor, BaseImageProcessor)
        and hasattr(feature_extractor, "size")
        and isinstance(feature_extractor.size, dict)
    ):
        largest_image_size = max(feature_extractor.size.values())
        if largest_image_size > 64:
            # hardcoded exceptions
            models_with_large_image_size = ("deformable_detr", "flava", "grounding_dino", "mgp_str", "swiftformer")
            if any(model_name in tiny_config.model_type for model_name in models_with_large_image_size):
                pass

            # TODO: Disabling this might get very slow tests!! Need to check the run time !!!
            # else:
            #     raise ValueError(
            #         f"Image size of {tiny_config.model_type} is too large ({feature_extractor.size}). "
            #         "Please reduce it to 64 or less on each dimension. The following steps are usually the "
            #         "easiest solution: 1) confirm that you're setting `image_size` in your ModelTester class; "
            #         "2) ensure that it gets passed to the tester config init, `get_config()`."
            #     )

    return feature_extractor