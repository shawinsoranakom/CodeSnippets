def test_register_kv_caches_uniform_type(mock_get_layers, backend):
    """Test register_kv_caches with UniformTypeKVCacheSpecs.

    Two attention layers use the same backend but different num_kv_heads,
    giving them different per-layer page sizes. Each has its own
    KVCacheTensor and are wrapped in a UniformTypeKVCacheSpecs group.
    Verifies that each layer gets the correct tensor_idx and
    page_size_bytes in its block data ref.
    """
    from vllm.v1.worker.utils import AttentionGroup

    backend_cls = AttentionBackendEnum[backend].get_class()

    layer_a = "model.layers.0.self_attn"
    layer_b = "model.layers.1.self_attn"
    spec_a = FullAttentionSpec(
        block_size=BLOCK_SIZE,
        num_kv_heads=NUM_KV_HEADS,
        head_size=HEAD_SIZE,
        dtype=DTYPE,
    )
    spec_b = FullAttentionSpec(
        block_size=BLOCK_SIZE,
        num_kv_heads=NUM_KV_HEADS * 2,
        head_size=HEAD_SIZE,
        dtype=DTYPE,
    )
    assert spec_a.page_size_bytes != spec_b.page_size_bytes

    uniform_spec = UniformTypeKVCacheSpecs(
        block_size=BLOCK_SIZE,
        kv_cache_specs={layer_a: spec_a, layer_b: spec_b},
    )

    kv_cache_config = KVCacheConfig(
        num_blocks=NUM_BLOCKS,
        kv_cache_tensors=[
            KVCacheTensor(
                size=spec_a.page_size_bytes * NUM_BLOCKS,
                shared_by=[layer_a],
            ),
            KVCacheTensor(
                size=spec_b.page_size_bytes * NUM_BLOCKS,
                shared_by=[layer_b],
            ),
        ],
        kv_cache_groups=[
            KVCacheGroupSpec(
                layer_names=[layer_a, layer_b],
                kv_cache_spec=uniform_spec,
            )
        ],
    )

    attn_groups = [
        [
            AttentionGroup(
                backend=backend_cls,
                layer_names=[layer_a],
                kv_cache_spec=spec_a,
                kv_cache_group_id=0,
            ),
            AttentionGroup(
                backend=backend_cls,
                layer_names=[layer_b],
                kv_cache_spec=spec_b,
                kv_cache_group_id=0,
            ),
        ]
    ]

    kv_caches = _allocate_and_reshape_kv_caches(
        kv_cache_config,
        attn_groups,
        device=torch.device("cuda:0"),
    )

    mock_get_layers.return_value = {
        layer_a: _make_mock_layer(backend_cls),
        layer_b: _make_mock_layer(backend_cls),
    }

    worker, spec = _make_worker(kv_cache_config)
    worker.register_kv_caches(kv_caches)

    canonical = spec.get_handlers.call_args[0][0]
    assert isinstance(canonical, CanonicalKVCaches)

    unbinds = backend_cls.get_name() in ("FLASH_ATTN", "FLEX_ATTENTION")
    tensors_per_layer = 2 if unbinds else 1

    for block_tensor in canonical.tensors:
        assert block_tensor.tensor.dtype == torch.int8

    # Single group with refs from both layers
    assert len(canonical.group_data_refs) == 1
    group_refs = canonical.group_data_refs[0]
    assert len(group_refs) == 2 * tensors_per_layer

    if unbinds:
        half_a = spec_a.page_size_bytes // 2
        half_b = spec_b.page_size_bytes // 2

        assert len(canonical.tensors) == 4
        assert canonical.tensors[0].page_size_bytes == half_a
        assert canonical.tensors[1].page_size_bytes == half_a
        assert canonical.tensors[2].page_size_bytes == half_b
        assert canonical.tensors[3].page_size_bytes == half_b
        assert canonical.tensors[0].tensor.shape == (NUM_BLOCKS, half_a)
        assert canonical.tensors[1].tensor.shape == (NUM_BLOCKS, half_a)
        assert canonical.tensors[2].tensor.shape == (NUM_BLOCKS, half_b)
        assert canonical.tensors[3].tensor.shape == (NUM_BLOCKS, half_b)

        assert group_refs[0] == CanonicalKVCacheRef(
            tensor_idx=0, page_size_bytes=half_a
        )
        assert group_refs[1] == CanonicalKVCacheRef(
            tensor_idx=1, page_size_bytes=half_a
        )
        assert group_refs[2] == CanonicalKVCacheRef(
            tensor_idx=2, page_size_bytes=half_b
        )
        assert group_refs[3] == CanonicalKVCacheRef(
            tensor_idx=3, page_size_bytes=half_b
        )
    else:
        assert len(canonical.tensors) == 2
        assert canonical.tensors[0].page_size_bytes == spec_a.page_size_bytes
        assert canonical.tensors[1].page_size_bytes == spec_b.page_size_bytes
        assert canonical.tensors[0].tensor.shape == (NUM_BLOCKS, spec_a.page_size_bytes)
        assert canonical.tensors[1].tensor.shape == (NUM_BLOCKS, spec_b.page_size_bytes)

        assert group_refs[0] == CanonicalKVCacheRef(
            tensor_idx=0, page_size_bytes=spec_a.page_size_bytes
        )
        assert group_refs[1] == CanonicalKVCacheRef(
            tensor_idx=1, page_size_bytes=spec_b.page_size_bytes
        )