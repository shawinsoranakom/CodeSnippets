def create_kv_caches_with_random_flash(
    num_blocks: int,
    block_size: int,
    num_layers: int,
    num_heads: int,
    head_size: int,
    cache_dtype: str | torch.dtype | None,
    model_dtype: str | torch.dtype | None = None,
    seed: int | None = None,
    device: str | None = "cuda",
    cache_layout: str | None = "NHD",
) -> tuple[list[torch.Tensor], list[torch.Tensor]]:
    set_random_seed(seed)

    dtype = get_kv_cache_torch_dtype(cache_dtype, model_dtype)
    generic_kv_cache_shape = (num_blocks, 2, block_size, num_heads, head_size)
    assert cache_layout in ("NHD", "HND")
    stride_order = (0, 1, 2, 3, 4) if cache_layout == "NHD" else (0, 1, 3, 2, 4)

    kv_cache_allocation_shape = tuple(generic_kv_cache_shape[i] for i in stride_order)
    scale = head_size**-0.5

    key_caches: list[torch.Tensor] = []
    value_caches: list[torch.Tensor] = []

    for _ in range(num_layers):
        if cache_dtype == "nvfp4":
            # Full page dim: fp4 data + fp8 block scales per head.
            # Per page layout: [K_data | K_scale | V_data | V_scale]
            # Returns [:, 0] and [:, 1] like all other dtypes.
            full_dim = nvfp4_kv_cache_full_dim(head_size)
            nvfp4_shape = (num_blocks, 2, block_size, num_heads, full_dim)
            nvfp4_phys = tuple(nvfp4_shape[i] for i in stride_order)
            inv = [stride_order.index(i) for i in range(len(stride_order))]
            key_value_cache = torch.randint(
                0,
                256,
                nvfp4_phys,
                dtype=dtype,
                device=device,
            ).permute(*inv)
        else:
            key_value_cache = torch.empty(
                size=kv_cache_allocation_shape, dtype=dtype, device=device
            ).permute(*stride_order)
            if cache_dtype in ["auto", "half", "bfloat16", "float"]:
                key_value_cache.uniform_(-scale, scale)
            elif cache_dtype == "fp8":
                _generate_random_fp8(key_value_cache, -scale, scale)
            else:
                raise ValueError(f"Does not support key cache of type {cache_dtype}")
        key_caches.append(key_value_cache[:, 0])
        value_caches.append(key_value_cache[:, 1])
    return key_caches, value_caches