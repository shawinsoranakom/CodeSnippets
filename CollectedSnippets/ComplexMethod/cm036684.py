def test_reshape_and_cache_flash(
    kv_cache_factory_flashinfer,
    num_tokens: int,
    num_heads: int,
    head_size: int,
    block_size: int,
    num_blocks: int,
    dtype: torch.dtype,
    seed: int,
    device: str,
    kv_cache_dtype: str,
    kv_cache_layout: str,
    kv_scale_type: str,
    implementation: str,
) -> None:
    set_random_seed(seed)
    torch.set_default_device(device)
    torch.accelerator.set_device_index(device)
    assert implementation in ["cuda", "triton"]
    if implementation == "triton" and kv_cache_layout == "HND":
        pytest.skip("Triton implementation only supports NHD layout.")

    if kv_scale_type == "attn_head" and implementation != "cuda":
        pytest.skip("Only CUDA implementation supports attn_head scaling.")

    if kv_cache_dtype == "nvfp4":
        if not current_platform.has_device_capability(100):
            pytest.skip("NVFP4 requires compute capability >= 10.0 (Blackwell).")
        if implementation != "cuda":
            pytest.skip("NVFP4 only supports CUDA implementation.")
        if kv_scale_type != "tensor":
            pytest.skip("NVFP4 only supports per-tensor scaling.")
        if head_size % 16 != 0:
            pytest.skip("NVFP4 requires head_size divisible by 16.")
        if (head_size // 16) % 4 != 0:
            pytest.skip(
                "NVFP4 requires (head_size // 16) divisible by 4 "
                "for 4x4 block scale swizzle."
            )
        if block_size % 4 != 0:
            pytest.skip("NVFP4 requires block_size divisible by 4.")
        if dtype not in (torch.float16, torch.bfloat16):
            pytest.skip("NVFP4 quantization only supports fp16/bf16 input.")

    # fp8 conversion requires continugous memory buffer. Reduce the number of
    # blocks and tokens to consume less memory.
    num_tokens = num_tokens // 2
    num_blocks = num_blocks // 2
    # Create a random slot mapping.
    num_slots = block_size * num_blocks
    slot_mapping_lst = random.sample(range(num_slots), num_tokens)
    slot_mapping = torch.tensor(slot_mapping_lst, dtype=torch.long, device=device)
    qkv = torch.randn(num_tokens, 3, num_heads, head_size, dtype=dtype, device=device)
    _, key, value = qkv.unbind(dim=1)

    # Create the KV caches.
    key_caches, value_caches = kv_cache_factory_flashinfer(
        num_blocks,
        block_size,
        1,
        num_heads,
        head_size,
        kv_cache_dtype,
        dtype,
        device=device,
        cache_layout=kv_cache_layout,
    )
    key_cache, value_cache = key_caches[0], value_caches[0]
    del key_caches
    del value_caches

    # For nvfp4, the factory returns kv[:, 0] and kv[:, 1] like all dtypes.
    # Split views are still needed for dequant verification.
    key_scale_cache = None
    value_scale_cache = None
    nvfp4_key_data = None
    nvfp4_value_data = None
    if kv_cache_dtype == "nvfp4":
        (nvfp4_key_data,), (key_scale_cache,) = nvfp4_kv_cache_split_views(key_cache)
        (nvfp4_value_data,), (value_scale_cache,) = nvfp4_kv_cache_split_views(
            value_cache
        )

    if kv_cache_dtype == "nvfp4":
        # Global scale = amax / 448 (per-tensor)
        k_scale = (key.abs().amax() / 448.0).to(torch.float32)
        v_scale = (value.abs().amax() / 448.0).to(torch.float32)
    elif kv_scale_type == "tensor":
        k_scale = (key.amax() / 64.0).to(torch.float32)
        v_scale = (value.amax() / 64.0).to(torch.float32)
    else:  # "attn_head"
        k_scale = (key.amax(dim=(0, 2)) / 64.0).to(torch.float32)
        v_scale = (value.amax(dim=(0, 2)) / 64.0).to(torch.float32)

    def permute_and_compact(x):
        y = x if kv_cache_layout == "NHD" else x.permute(0, 2, 1, 3)
        return y.contiguous()

    if kv_cache_dtype != "nvfp4":
        key_cache_compact = permute_and_compact(key_cache)
        value_cache_compact = permute_and_compact(value_cache)

    def convert_fp8_local(output, input, scale, kv_dtype):
        fp8_input = input.view(current_platform.fp8_dtype())
        if scale.numel() == 1:  # per-tensor
            result = scaled_dequantize(
                fp8_input.flatten(0, 2), scale, group_shape=None, out_dtype=output.dtype
            ).reshape(*input.shape)
        else:  # per-head: broadcast scale along the head dimension
            # Original code uses dim 2 for NHD, dim 1 for HND
            if kv_cache_layout == "NHD":
                result = fp8_input.to(output.dtype) * scale.view(1, 1, -1, 1)
            else:
                result = fp8_input.to(output.dtype) * scale.view(1, -1, 1, 1)
        output.copy_(result)

    # Clone the KV caches (for non-nvfp4, used as reference baseline).
    if kv_cache_dtype == "fp8":
        cloned_key_cache = torch.empty_like(key_cache_compact, dtype=torch.float16)
        convert_fp8_local(cloned_key_cache, key_cache_compact, k_scale, kv_cache_dtype)
        cloned_value_cache = torch.empty_like(value_cache_compact, dtype=torch.float16)
        convert_fp8_local(
            cloned_value_cache, value_cache_compact, v_scale, kv_cache_dtype
        )
    elif kv_cache_dtype != "nvfp4":
        cloned_key_cache = key_cache_compact.clone()
        cloned_value_cache = value_cache_compact.clone()

    # Call the reshape_and_cache kernel.
    if implementation == "cuda":
        if kv_cache_dtype != "nvfp4":
            opcheck(
                torch.ops._C_cache_ops.reshape_and_cache_flash,
                (
                    key,
                    value,
                    key_cache,
                    value_cache,
                    slot_mapping,
                    kv_cache_dtype,
                    k_scale,
                    v_scale,
                ),
                cond=(head_size == HEAD_SIZES[0]),
            )
        ops.reshape_and_cache_flash(
            key,
            value,
            key_cache,
            value_cache,
            slot_mapping,
            kv_cache_dtype,
            k_scale,
            v_scale,
        )
    elif implementation == "triton":
        from vllm.v1.attention.ops.triton_reshape_and_cache_flash import (
            triton_reshape_and_cache_flash,
        )

        triton_reshape_and_cache_flash(
            key,
            value,
            key_cache,
            value_cache,
            slot_mapping,
            kv_cache_dtype,
            k_scale,
            v_scale,
        )

    if kv_cache_dtype == "nvfp4":
        # Verify NVFP4 by dequantizing the entire cache and comparing
        # the written positions against original bf16 values.
        # Same pattern as FP8: dequant whole cache, then extract and compare.
        from tests.kernels.quantization.nvfp4_utils import (
            dequant_nvfp4_kv_cache,
        )

        def dequant_nvfp4_cache_nhd(data_cache, scale_cache, global_scale):
            # data_cache:  [N, T, H, data_dim]  NHD (contiguous inner dims)
            # scale_cache: [N, T, H, scale_dim] NHD (contiguous inner dims)
            # Permute to HND layout for the dequant utility.
            data_hnd = data_cache.permute(0, 2, 1, 3)
            scale_hnd = scale_cache.permute(0, 2, 1, 3)
            result_hnd = dequant_nvfp4_kv_cache(
                data_hnd, scale_hnd, global_scale, head_size, block_size
            )
            return result_hnd.permute(0, 2, 1, 3)  # back to [N, T, H, D]

        result_key_cache = dequant_nvfp4_cache_nhd(
            nvfp4_key_data, key_scale_cache, k_scale.item()
        )
        result_value_cache = dequant_nvfp4_cache_nhd(
            nvfp4_value_data, value_scale_cache, v_scale.item()
        )

        # Flatten [num_blocks, block_size] → [num_slots] and index by slot_mapping.
        num_slots = num_blocks * block_size
        result_key_flat = result_key_cache.reshape(num_slots, num_heads, head_size)
        result_value_flat = result_value_cache.reshape(num_slots, num_heads, head_size)

        torch.testing.assert_close(
            result_key_flat[slot_mapping], key.float(), atol=1.5, rtol=0.5
        )
        torch.testing.assert_close(
            result_value_flat[slot_mapping], value.float(), atol=1.5, rtol=0.5
        )
        return

    key_cache_compact = permute_and_compact(key_cache)
    value_cache_compact = permute_and_compact(value_cache)

    if kv_cache_dtype == "fp8":
        result_key_cache = torch.empty_like(key_cache_compact, dtype=torch.float16)
        convert_fp8_local(result_key_cache, key_cache_compact, k_scale, kv_cache_dtype)
        result_value_cache = torch.empty_like(value_cache_compact, dtype=torch.float16)
        convert_fp8_local(
            result_value_cache,
            value_cache_compact,
            v_scale,
            kv_cache_dtype,
        )

    # Run the reference implementation.
    block_indices = torch.div(slot_mapping, block_size, rounding_mode="floor")
    block_indices_lst = block_indices.cpu().tolist()
    block_offsets = slot_mapping % block_size
    block_offsets_lst = block_offsets.cpu().tolist()
    for i in range(num_tokens):
        block_idx = block_indices_lst[i]
        block_offset = block_offsets_lst[i]
        if kv_cache_layout == "NHD":
            cloned_key_cache[block_idx, block_offset, :, :] = key[i]
            cloned_value_cache[block_idx, block_offset, :, :] = value[i]
        else:
            cloned_key_cache[block_idx, :, block_offset, :] = key[i]
            cloned_value_cache[block_idx, :, block_offset, :] = value[i]

    if kv_cache_dtype == "fp8":
        torch.testing.assert_close(
            result_key_cache, cloned_key_cache, atol=0.001, rtol=0.1
        )
        torch.testing.assert_close(
            result_value_cache, cloned_value_cache, atol=0.001, rtol=0.1
        )
    else:
        torch.testing.assert_close(key_cache_compact, cloned_key_cache)
        torch.testing.assert_close(value_cache_compact, cloned_value_cache)