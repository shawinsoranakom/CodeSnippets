def _get_shrink_lora_scale_ptr(
    lora_scale_weights: list[torch.Tensor], device: torch.device
):
    """
    `_SHRINK_LORA_SCALE_PTR_DICT` collects the required information during
    `profile_run`. After this, it remains constant and subsequent usage is
    through LUT.

    Returns a tuple of (scale_ptr_tensor, l_stride, n_stride, k_stride).

    Supports scale tensors of varying dimensionality:
    - 1D: (lora_num,) — tensor-wise quantization
    - 2D: (lora_num, N) — per-channel quantization
    - 3D: (lora_num, N, K) — block-wise quantization
    - 4D: (lora_num, 1, N, K) — block-wise with extra dim (squeezed to 3D)

    Refer to:
    https://github.com/triton-lang/triton/blob/release/3.1.x/python/tutorials/08-grouped-gemm.py
    """
    key = tuple(lora_weight.data_ptr() for lora_weight in lora_scale_weights)

    if values := _SHRINK_LORA_SCALE_PTR_DICT.get(key):
        return values

    tensor_ptrs = []
    scale_l_strides = []
    scale_n_strides = []
    scale_k_strides = []
    for lora_scale_weight in lora_scale_weights:
        if lora_scale_weight.ndim == 4:  # shape:(lora_num,1,size,rank)
            assert lora_scale_weight.size(1) == 1
            lora_scale_weight = lora_scale_weight.squeeze(dim=1)
        assert 1 <= lora_scale_weight.ndim <= 3
        assert lora_scale_weight.is_contiguous()
        tensor_ptrs.append(lora_scale_weight.data_ptr())
        scale_l_strides.append(
            lora_scale_weight.stride(0) if lora_scale_weight.ndim > 0 else 0
        )
        scale_n_strides.append(
            lora_scale_weight.stride(-2)
            if lora_scale_weight.ndim > 2
            else (lora_scale_weight.stride(-1) if lora_scale_weight.ndim > 1 else 1)
        )
        scale_k_strides.append(
            lora_scale_weight.stride(-1) if lora_scale_weight.ndim > 2 else 0
        )
    if len(lora_scale_weights) > 1:
        scale_ptr_tensor = torch.tensor(tensor_ptrs, device=device, dtype=torch.uint64)
    else:
        scale_ptr_tensor = lora_scale_weights[0]

    if (
        len(set(scale_l_strides)) > 1
        or len(set(scale_n_strides)) > 1
        or len(set(scale_k_strides)) > 1
    ):
        raise ValueError("All LoRA scale weights must have the same stride.")

    _SHRINK_LORA_SCALE_PTR_DICT[key] = (
        scale_ptr_tensor,
        scale_l_strides[0],
        scale_n_strides[0],
        scale_k_strides[0],
    )
    return _SHRINK_LORA_SCALE_PTR_DICT.get(key)