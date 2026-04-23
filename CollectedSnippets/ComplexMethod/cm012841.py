def check_min_max_valid(min_val: torch.Tensor, max_val: torch.Tensor) -> bool:
    """Checks if the given minimum and maximum values are valid, meaning that
    they exist and the min value is less than the max value.
    """
    if min_val.numel() == 0 or max_val.numel() == 0:
        warnings.warn(
            "must run observer before calling calculate_qparams. "
            + "Returning default values.",
            stacklevel=2,
        )
        return False

    if min_val.dim() == 0 or max_val.dim() == 0:
        if min_val == float("inf") and max_val == float("-inf"):
            warnings.warn(
                "must run observer before calling calculate_qparams. "
                + "Returning default values.",
                stacklevel=2,
            )

            return False

        if min_val > max_val:
            raise AssertionError(f"min {min_val} should be less than max {max_val}")
    else:
        if torch.any(min_val > max_val):
            raise AssertionError(f"min {min_val} should be less than max {max_val}")

    return True