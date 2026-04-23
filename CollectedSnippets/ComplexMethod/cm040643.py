def _rescale_dataset_split_sizes(left_size, right_size, total_length):
    """Rescale the dataset split sizes.

    We want to ensure that the sum of
    the split sizes is equal to the total length of the dataset.

    Args:
        left_size: The size of the left dataset split.
        right_size: The size of the right dataset split.
        total_length: The total length of the dataset.

    Returns:
        tuple: A tuple of rescaled `left_size` and `right_size` integers.
    """
    left_size_type = type(left_size)
    right_size_type = type(right_size)

    # check both left_size and right_size are integers or floats
    if (left_size is not None and left_size_type not in [int, float]) and (
        right_size is not None and right_size_type not in [int, float]
    ):
        raise TypeError(
            "Invalid `left_size` and `right_size` Types. Expected: "
            "integer or float or None, Received: type(left_size)="
            f"{left_size_type} and type(right_size)={right_size_type}"
        )

    # check left_size is a integer or float
    if left_size is not None and left_size_type not in [int, float]:
        raise TypeError(
            "Invalid `left_size` Type. Expected: int or float or None, "
            f"Received: type(left_size)={left_size_type}.  "
        )

    # check right_size is a integer or float
    if right_size is not None and right_size_type not in [int, float]:
        raise TypeError(
            "Invalid `right_size` Type. "
            "Expected: int or float or None,"
            f"Received: type(right_size)={right_size_type}."
        )

    # check left_size and right_size are non-zero
    if left_size == 0 and right_size == 0:
        raise ValueError(
            "Both `left_size` and `right_size` are zero. "
            "At least one of the split sizes must be non-zero."
        )

    # check left_size is non-negative and less than 1 and less than total_length
    if (
        left_size_type is int
        and (left_size <= 0 or left_size >= total_length)
        or left_size_type is float
        and (left_size <= 0 or left_size >= 1)
    ):
        raise ValueError(
            "`left_size` should be either a positive integer "
            f"smaller than {total_length}, or a float "
            "within the range `[0, 1]`. Received: left_size="
            f"{left_size}"
        )

    # check right_size is non-negative and less than 1 and less than
    # total_length
    if (
        right_size_type is int
        and (right_size <= 0 or right_size >= total_length)
        or right_size_type is float
        and (right_size <= 0 or right_size >= 1)
    ):
        raise ValueError(
            "`right_size` should be either a positive integer "
            f"and smaller than {total_length} or a float "
            "within the range `[0, 1]`. Received: right_size="
            f"{right_size}"
        )

    # check sum of left_size and right_size is less than or equal to
    # total_length
    if (
        right_size_type is left_size_type is float
        and right_size + left_size > 1
    ):
        raise ValueError(
            "The sum of `left_size` and `right_size` is greater "
            "than 1. It must be less than or equal to 1."
        )

    if left_size_type is float:
        left_size = round(left_size * total_length)
    elif left_size_type is int:
        left_size = float(left_size)

    if right_size_type is float:
        right_size = round(right_size * total_length)
    elif right_size_type is int:
        right_size = float(right_size)

    if left_size is None:
        left_size = total_length - right_size
    elif right_size is None:
        right_size = total_length - left_size

    if left_size + right_size > total_length:
        raise ValueError(
            "The sum of `left_size` and `right_size` should "
            f"be smaller than the {total_length}. "
            f"Received: left_size + right_size = {left_size + right_size}"
            f"and total_length = {total_length}"
        )

    for split, side in [(left_size, "left"), (right_size, "right")]:
        if split == 0:
            raise ValueError(
                f"With `dataset` of length={total_length}, `left_size`="
                f"{left_size} and `right_size`={right_size}."
                f"Resulting {side} side dataset split will be empty. "
                "Adjust any of the aforementioned parameters"
            )

    left_size, right_size = int(left_size), int(right_size)
    return left_size, right_size