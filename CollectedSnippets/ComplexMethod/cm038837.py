def _get_lora_a_ptr(lora_a_weights: list[torch.Tensor], device: torch.device):
    """
    `_LORA_A_PTR_DICT` collects the required information during `profile_run`,
    After this, it remains constant and subsequent usage is through LUT.
    Refer to:
    https://github.com/triton-lang/triton/blob/release/3.1.x/python/tutorials/08-grouped-gemm.py
    """
    key = tuple(lora_weight.data_ptr() for lora_weight in lora_a_weights)

    if values := _LORA_A_PTR_DICT.get(key):
        return values

    lora_strides_d0 = []
    lora_strides_d1 = []
    lora_strides_d2 = []
    tensor_ptrs = []
    for lora_a_weight in lora_a_weights:
        if lora_a_weight.ndim == 4:  # shape:(lora_num,1,size,rank)
            assert lora_a_weight.size(1) == 1
            lora_a_weight = lora_a_weight.squeeze(dim=1)
        else:
            assert lora_a_weight.ndim == 3  # shape:(lora_num,size,rank)
        assert lora_a_weight.is_contiguous()
        tensor_ptrs.append(lora_a_weight.data_ptr())
        lora_strides_d0.append(lora_a_weight.stride(0))
        lora_strides_d1.append(lora_a_weight.stride(1))
        lora_strides_d2.append(lora_a_weight.stride(2))
    if len(lora_a_weights) > 1:
        lora_ptr_tensor = torch.tensor(tensor_ptrs, device=device, dtype=torch.uint64)
    else:
        lora_ptr_tensor = lora_a_weights[0]

    if (
        len(set(lora_strides_d0)) > 1
        or len(set(lora_strides_d1)) > 1
        or len(set(lora_strides_d2)) > 1
    ):
        raise ValueError("All LoRA weights must have the same stride.")

    _LORA_A_PTR_DICT[key] = (
        lora_ptr_tensor,
        lora_strides_d0[0],
        lora_strides_d1[0],
        lora_strides_d2[0],
    )
    return _LORA_A_PTR_DICT.get(key)