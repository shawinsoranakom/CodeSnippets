def can_use_triton_kernel(
    mat_a: TensorBox,
    mat_b: TensorBox,
    offs: TensorBox | None,
    bias: TensorBox | None,
    scale_result: TensorBox | None,
) -> bool:
    if not (
        torch.cuda.is_available()
        and torch.cuda.get_device_capability() >= (9, 0)
        and not torch.version.hip
    ):
        return False
    if not has_triton():
        return False

    # The _grouped_mm()/_scaled_grouped_mm() operator do not support
    # bias nor scale_result yet.
    if bias is not None:
        return False
    if scale_result is not None:
        return False

    if len(mat_a.get_size()) == 2 or len(mat_b.get_size()) == 2:
        return offs is not None
    else:
        return offs is None