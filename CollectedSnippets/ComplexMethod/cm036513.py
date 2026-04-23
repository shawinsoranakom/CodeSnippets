def get_wrapped_test_sizes(
    test_info: VLMTestInfo, test_type: VLMTestType
) -> tuple[ImageSizeWrapper, ...]:
    """Given a test info which may have size factors or fixed sizes, wrap them
    and combine them into an iterable, each of which will be used in parameter
    expansion.

    Args:
        test_info: Test configuration to be expanded.
        test_type: The type of test being filtered for.
    """
    # If it is an embedding test, we always use the EMBEDDING_SIZE_FACTORS
    if test_type == VLMTestType.EMBEDDING:
        return tuple(
            [
                ImageSizeWrapper(type=SizeType.SIZE_FACTOR, data=factor)
                for factor in EMBEDDING_SIZE_FACTORS
            ]
        )
    # Audio and Custom inputs have preprocessed inputs
    elif test_type in (VLMTestType.AUDIO, VLMTestType.CUSTOM_INPUTS):
        return tuple()

    size_factors = test_info.image_size_factors if test_info.image_size_factors else []
    fixed_sizes = test_info.image_sizes if test_info.image_sizes else []

    wrapped_factors = [
        ImageSizeWrapper(type=SizeType.SIZE_FACTOR, data=factor)
        for factor in size_factors
    ]

    wrapped_sizes = [
        ImageSizeWrapper(type=SizeType.FIXED_SIZE, data=size) for size in fixed_sizes
    ]

    return tuple(wrapped_factors + wrapped_sizes)