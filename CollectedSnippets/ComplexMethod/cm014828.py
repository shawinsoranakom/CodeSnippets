def _check_equal(
    golden: torch.Tensor,
    reference: torch.Tensor,
    test: torch.Tensor,
    fudge_factor: float,
    tensor_name: str | None = None
) -> None:
    """
    Compare test tensor against golden and reference tensors.
    Golden is the highest precision possible serving as the "ground truth"
    Reference is the same precision as test and should also serve as less precisie ground truth.
    We calcculate the "reference error" by comparing the golden to reference and use this as the
    measruing stick for the test tensor.

    Raises ValueError if compiled error exceeds threshold.

    Args:
        golden (torch.Tensor): The golden tensor to compare against.
        reference (torch.Tensor): The reference tensor for error calculation.
        test (torch.Tensor): The test tensor to be evaluated.
        fudge_factor (float): A multiplier for the reference error to determine the threshold.
        tensor_name (Optional[str], optional): Name of the tensor for error reporting. Defaults to None.

    Raises:
        ValueError: If the test tensor contains NaN values while the reference does not,
                    or if the test error exceeds the calculated threshold.

    Notes:
        - For nested tensors, the function recursively calls itself on each nested element.
        - The error threshold is calculated as the maximum of a default tolerance for float32
          and the product of the reference error and the fudge_factor.
        - If the test error exceeds the threshold, a ValueError is raised with a detailed message.
    """
    if golden.is_nested and reference.is_nested and test.is_nested:
        for gold, ref, tst in zip(golden.unbind(), reference.unbind(), test.unbind()):
            _check_equal(gold, ref, tst, fudge_factor, tensor_name)
        return

    # Compute error between golden
    test_error = (golden - test).abs().max()
    ref_error = (golden - reference).abs().max()

    if torch.isnan(test_error).any() and not torch.isnan(ref_error).any():
        raise ValueError("Output/Grad with NaN")

    # Calculate the error threshold as the maximum of:
    # 1. A predefined default tolerance for float32
    # 2. The reference error multiplied by the fudge factor
    threshold = max(default_atol[torch.float32], ref_error * fudge_factor)
    if test_error > threshold:
        name = tensor_name or ""
        msg = f"{name} Test error {test_error} is greater than threshold {threshold}!"
        raise ValueError(msg)