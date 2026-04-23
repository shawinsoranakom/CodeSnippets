def get_block_size(
    input_shape: tuple[int, ...], granularity: Granularity
) -> tuple[int, ...]:
    """Get the block size based on the input shape and granularity type.

    Args:
        input_shape: The input tensor shape possibly more than 2 dimensions
        granularity: The granularity type of the quantization
    """
    if not isinstance(granularity, Granularity):
        raise AssertionError(
            "Please provide an instance of Granularity, not subclass of it"
        )
    if isinstance(granularity, PerTensor):
        return input_shape
    elif isinstance(granularity, PerAxis):
        block_size = list(input_shape)
        block_size[granularity.axis] = 1
        return tuple(block_size)
    elif isinstance(granularity, PerRow):
        return (1,) * (len(input_shape) - 1) + (input_shape[-1],)
    elif isinstance(granularity, PerGroup):
        if len(input_shape) != 2:
            raise AssertionError(
                f"Expecting input shape dim to be 2 for per group quantization, gotinput shape: {input_shape}"
            )
        return (1, granularity.group_size)
    elif isinstance(granularity, PerToken):
        block_size = [1] * len(input_shape)
        block_size[-1] = input_shape[-1]
        return tuple(block_size)
    raise ValueError(f"Unsupported Granularity: {granularity}")