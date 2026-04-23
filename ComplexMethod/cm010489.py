def is_sdpa_error(func: OpOverload, idx: int, e: Exception) -> bool:
    if (
        (
            func is aten._scaled_dot_product_flash_attention.default
            or func is aten._flash_attention_forward.default
        )
        and idx in (6, 7)
        and "Devices" in repr(e)
    ):
        return True
    if (
        (
            func is aten._scaled_dot_product_efficient_attention.default
            or func is aten._efficient_attention_forward.default
        )
        and idx in (2, 3)
        and "Devices" in repr(e)
    ):
        return True
    if (
        func is aten._scaled_dot_product_cudnn_attention.default
        and idx in (6, 7)
        and "Devices" in repr(e)
    ):
        return True
    return False