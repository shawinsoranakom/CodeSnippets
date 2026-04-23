def test_concat_and_cache_ds_mla(
    kv_lora_rank: int,
    qk_rope_head_dim: int,
    num_tokens: int,
    block_size: int,
    num_blocks: int,
    dtype: torch.dtype,
    seed: int,
    device: str,
) -> None:
    if current_platform.is_rocm():
        pytest.skip("concat_and_cache_mla doesn't support fp8_ds_mla on ROCm")
    if dtype.itemsize != 2:
        pytest.skip("ds_mla only supports 16-bit input")
    if kv_lora_rank != 512:
        pytest.skip("fp8_ds_mla requires kv_lora_rank == 512")
    kv_cache_dtype = "fp8_ds_mla"
    set_random_seed(seed)
    torch.set_default_device(device)
    torch.accelerator.set_device_index(device)

    total_slots = num_blocks * block_size
    slot_mapping_lst = random.sample(range(total_slots), num_tokens)
    slot_mapping = torch.tensor(slot_mapping_lst, dtype=torch.long, device=device)

    kv_c = torch.randn(num_tokens, kv_lora_rank, dtype=dtype, device=device)
    k_pe = torch.randn(num_tokens, qk_rope_head_dim, dtype=dtype, device=device)
    entry_size = kv_lora_rank + (4 * 4) + (2 * qk_rope_head_dim)

    scale = torch.tensor(1.0, dtype=torch.float32, device=device)
    kv_cache = _create_mla_cache(
        num_blocks,
        block_size,
        entry_size,
        dtype=torch.uint8,
        kv_cache_dtype=kv_cache_dtype,
        device=device,
    )

    ref_cache = torch.zeros_like(kv_cache, dtype=kv_cache.dtype)
    tile_data = torch.zeros(128, dtype=dtype, device=device)

    for i in range(num_tokens):
        slot = slot_mapping[i].item()
        block_idx = slot // block_size
        block_offset = slot % block_size

        ref_cache_slice = ref_cache[block_idx, block_offset]
        ref_cache_16bit = ref_cache_slice.view(dtype)
        ref_cache_32bit = ref_cache_slice.view(torch.float32)

        kv_c_data = kv_c[i]
        num_tiles = kv_lora_rank // 128
        for tile_idx in range(num_tiles):
            tile_start = tile_idx * 128
            tile_end = (tile_idx + 1) * 128
            tile_data[:] = kv_c_data[tile_start:tile_end]

            # tile_scale = tile_data.amax().to(torch.float32) / 448.
            # NOTE: Using torch's amax() gives different results,
            # so this must be manually computed.
            tile_data_float = tile_data.to(torch.float32)
            manual_max = abs(tile_data_float[0])
            for j in range(1, 128):
                manual_max = max(manual_max, abs(tile_data_float[j]))
            tile_scale = manual_max / 448.0

            ref_cache_32bit[kv_lora_rank // 4 + tile_idx] = tile_scale

            ops.convert_fp8(
                ref_cache_slice[tile_start:tile_end],
                tile_data,
                tile_scale.item(),
                kv_dtype="fp8",
            )

        for j in range(qk_rope_head_dim):
            ref_cache_16bit[kv_lora_rank // 2 + 8 + j] = k_pe[i, j]

    opcheck(
        torch.ops._C_cache_ops.concat_and_cache_mla,
        (kv_c, k_pe, kv_cache, slot_mapping, kv_cache_dtype, scale),
        test_utils=DEFAULT_OPCHECK_TEST_UTILS,
    )

    ops.concat_and_cache_mla(kv_c, k_pe, kv_cache, slot_mapping, kv_cache_dtype, scale)

    for i in range(num_tokens):
        slot = slot_mapping[i].item()
        block_idx = slot // block_size
        block_offset = slot % block_size
        kv_cache_slice = kv_cache[block_idx, block_offset]
        ref_cache_slice = ref_cache[block_idx, block_offset]

        kv_nope = kv_cache_slice[:kv_lora_rank]
        ref_nope = ref_cache_slice[:kv_lora_rank]
        kv_scales = kv_cache_slice.view(torch.float32)[
            kv_lora_rank // 4 : kv_lora_rank // 4 + 4
        ]
        ref_scales = ref_cache_slice.view(torch.float32)[
            kv_lora_rank // 4 : kv_lora_rank // 4 + 4
        ]
        kv_rope = kv_cache_slice.view(dtype)[kv_lora_rank // 2 + 8 :]
        ref_rope = ref_cache_slice.view(dtype)[kv_lora_rank // 2 + 8 :]

        torch.testing.assert_close(kv_nope, ref_nope, atol=0.001, rtol=0.1)
        torch.testing.assert_close(kv_scales, ref_scales, atol=0.001, rtol=0.1)
        torch.testing.assert_close(kv_rope, ref_rope, atol=0.001, rtol=0.1)