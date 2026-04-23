def assert_tensor_metadata(
    fake_mode: FakeTensorMode,
    func: OpOverload,
    t: FakeTensor,
    sizes: torch.Size | None = None,
    strides: tuple[int, ...] | None = None,
    dtype: torch.dtype | None = None,
    *,
    device: torch.device | None = None,
    layout: torch.layout | None = None,
) -> None:
    if sizes is not None:
        if t.size() != sizes:
            raise AssertionError(
                f"Tensor sizes mismatch! Expected: {sizes}, Got: {t.size()}"
            )
    if strides is not None:
        if t.stride() != strides:
            raise AssertionError(
                f"Tensor strides mismatch! Expected: {strides}, Got: {t.stride()}"
            )
    if dtype is not None:
        if t.dtype != dtype:
            raise AssertionError(
                f"Tensor dtype mismatch! Expected: {dtype}, Got: {t.dtype}"
            )
    if layout is not None:
        if t.layout != layout:
            raise AssertionError(
                f"Tensor layout mismatch! Expected: {layout}, Got: {t.layout}"
            )
    if device is not None:
        if t.device != device:
            raise AssertionError(
                f"Tensor device mismatch! Expected: {device}, Got: {t.device}"
            )