def spatial_3d_padding(x, padding=((1, 1), (1, 1), (1, 1)), data_format=None):
    """DEPRECATED."""
    if (
        len(padding) != 3
        or len(padding[0]) != 2
        or len(padding[1]) != 2
        or len(padding[2]) != 2
    ):
        raise ValueError(
            "Expected `padding` to be a tuple of 3 tuples of 2 integers. "
            f"Received: padding={padding}"
        )
    if data_format is None:
        data_format = backend.image_data_format()
    if data_format not in {"channels_first", "channels_last"}:
        raise ValueError(f"Unknown data_format: {data_format}")

    if data_format == "channels_first":
        pattern = [
            [0, 0],
            [0, 0],
            [padding[0][0], padding[0][1]],
            [padding[1][0], padding[1][1]],
            [padding[2][0], padding[2][1]],
        ]
    else:
        pattern = [
            [0, 0],
            [padding[0][0], padding[0][1]],
            [padding[1][0], padding[1][1]],
            [padding[2][0], padding[2][1]],
            [0, 0],
        ]
    return tf.compat.v1.pad(x, pattern)