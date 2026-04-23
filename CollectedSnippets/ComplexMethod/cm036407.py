def test_register_kv_caches(mock_get_layers, backend):
    """Test register_kv_caches with multiple groups covering all layer types.

    Creates one FullAttention group, one MLA group, one Mamba group, and
    one Mamba-padded group. Each group has GROUP_SIZE layers.

    KVCacheTensors are shared across all groups mirroring the real allocation
    in kv_cache_utils.py: tensor i is shared by layer i from every group.
    The padded-mamba group has a different page size so its layers get their
    own dedicated tensors.

    Uses the real GPUModelRunner.initialize_kv_cache_tensors to produce
    kv_caches, which automatically applies
    _update_hybrid_attention_mamba_layout for hybrid models.

    Verifies that the canonicalized CanonicalKVCaches has the correct
    block tensors, tensor_idx references, and page sizes across all groups.
    """
    from vllm.v1.attention.backends.mla.indexer import (
        DeepseekV32IndexerBackend,
    )
    from vllm.v1.worker.utils import AttentionGroup

    MLA_HEAD_SIZE = NUM_KV_HEADS * HEAD_SIZE * 2

    # padded mamba (missing HEAD_SIZE)
    CONV_STATE_SHAPE = (BLOCK_SIZE * NUM_KV_HEADS, HEAD_SIZE)
    UNALIGNED_SSM_STATE_SHAPE = (BLOCK_SIZE * NUM_KV_HEADS - 1, HEAD_SIZE)

    PAGE_SIZE_BYTES = 2 * BLOCK_SIZE * NUM_KV_HEADS * HEAD_SIZE * get_dtype_size(DTYPE)
    unaligned_mamba_page_size = PAGE_SIZE_BYTES - HEAD_SIZE * get_dtype_size(DTYPE)

    # unpadded mamba (fills page exactly)
    ALIGNED_SSM_STATE_SHAPE = (BLOCK_SIZE * NUM_KV_HEADS, HEAD_SIZE)

    backend_cls = AttentionBackendEnum[backend].get_class()

    attn_spec = FullAttentionSpec(
        block_size=BLOCK_SIZE,
        num_kv_heads=NUM_KV_HEADS,
        head_size=HEAD_SIZE,
        dtype=DTYPE,
    )
    mla_spec = MLAAttentionSpec(
        block_size=BLOCK_SIZE,
        num_kv_heads=1,
        head_size=MLA_HEAD_SIZE,
        dtype=DTYPE,
    )
    unaligned_mamba_spec = MambaSpec(
        block_size=BLOCK_SIZE,
        shapes=(CONV_STATE_SHAPE, UNALIGNED_SSM_STATE_SHAPE),
        dtypes=(DTYPE, DTYPE),
        page_size_padded=PAGE_SIZE_BYTES,
    )
    aligned_mamba_spec = MambaSpec(
        block_size=BLOCK_SIZE,
        shapes=(CONV_STATE_SHAPE, ALIGNED_SSM_STATE_SHAPE),
        dtypes=(DTYPE, DTYPE),
        page_size_padded=PAGE_SIZE_BYTES,
    )

    assert attn_spec.page_size_bytes == PAGE_SIZE_BYTES
    assert mla_spec.page_size_bytes == PAGE_SIZE_BYTES
    assert unaligned_mamba_spec.page_size_bytes == PAGE_SIZE_BYTES
    assert aligned_mamba_spec.page_size_bytes == PAGE_SIZE_BYTES

    GROUP_SIZE = 3

    # -- Build per-group layer info ----------------------------------------
    layer_idx = 0

    attn_layer_names = []
    for _ in range(GROUP_SIZE):
        attn_layer_names.append(f"model.layers.{layer_idx}.self_attn")
        layer_idx += 1

    mla_layer_names = []
    for _ in range(GROUP_SIZE):
        mla_layer_names.append(f"model.layers.{layer_idx}.self_attn")
        layer_idx += 1

    unaligned_mamba_layer_names = []
    for _ in range(GROUP_SIZE):
        unaligned_mamba_layer_names.append(f"model.layers.{layer_idx}.mamba_unpadded")
        layer_idx += 1

    aligned_mamba_layer_names = []
    for _ in range(GROUP_SIZE - 1):
        aligned_mamba_layer_names.append(f"model.layers.{layer_idx}.mamba_padded")
        layer_idx += 1

    layer_groups = [
        attn_layer_names,
        mla_layer_names,
        unaligned_mamba_layer_names,
        aligned_mamba_layer_names,
    ]

    kv_cache_tensors: list[KVCacheTensor] = []
    for i in range(GROUP_SIZE):
        shared_by: list[str] = []
        for group_layer_names in layer_groups:
            if len(group_layer_names) > i:
                shared_by.append(group_layer_names[i])
        kv_cache_tensors.append(
            KVCacheTensor(
                size=PAGE_SIZE_BYTES * NUM_BLOCKS,
                shared_by=shared_by,
            )
        )

    kv_cache_groups = [
        KVCacheGroupSpec(layer_names=attn_layer_names, kv_cache_spec=attn_spec),
        KVCacheGroupSpec(layer_names=mla_layer_names, kv_cache_spec=mla_spec),
        KVCacheGroupSpec(
            layer_names=unaligned_mamba_layer_names, kv_cache_spec=unaligned_mamba_spec
        ),
        KVCacheGroupSpec(
            layer_names=aligned_mamba_layer_names, kv_cache_spec=aligned_mamba_spec
        ),
    ]

    attn_groups = [
        [
            AttentionGroup(
                backend=backend_cls,
                layer_names=attn_layer_names,
                kv_cache_spec=attn_spec,
                kv_cache_group_id=0,
            ),
            AttentionGroup(
                backend=DeepseekV32IndexerBackend,
                layer_names=mla_layer_names,
                kv_cache_spec=mla_spec,
                kv_cache_group_id=1,
            ),
            AttentionGroup(
                backend=DeepseekV32IndexerBackend,  # unused for mamba
                layer_names=unaligned_mamba_layer_names,
                kv_cache_spec=unaligned_mamba_spec,
                kv_cache_group_id=2,
            ),
            AttentionGroup(
                backend=DeepseekV32IndexerBackend,  # unused for mamba
                layer_names=aligned_mamba_layer_names,
                kv_cache_spec=aligned_mamba_spec,
                kv_cache_group_id=3,
            ),
        ]
    ]

    kv_cache_config = KVCacheConfig(
        num_blocks=NUM_BLOCKS,
        kv_cache_tensors=kv_cache_tensors,
        kv_cache_groups=kv_cache_groups,
    )

    kv_caches = _allocate_and_reshape_kv_caches(
        kv_cache_config,
        attn_groups,
        device=torch.device("cuda:0"),
    )

    mock_layers: dict[str, MagicMock] = {}
    for layer_name in attn_layer_names:
        mock_layers[layer_name] = _make_mock_layer(backend_cls)
    for layer_name in mla_layer_names:
        mock_layers[layer_name] = _make_mock_layer(DeepseekV32IndexerBackend)
    mock_get_layers.return_value = mock_layers

    worker, spec = _make_worker(kv_cache_config)
    worker.register_kv_caches(kv_caches)

    canonical = spec.get_handlers.call_args[0][0]
    assert isinstance(canonical, CanonicalKVCaches)

    # -- Expected block tensors ----------------------------------------------
    # All tensors have the same padded page size (PAGE_SIZE_BYTES).
    # Tensor 0: shared by attn[0], mla[0], mamba_unaligned[0], mamba_aligned[0]
    # Tensor 1: shared by attn[1], mla[1], mamba_unaligned[1], mamba_aligned[1]
    # Tensor 2: shared by attn[2], mla[2], mamba_unaligned[2]
    #           (mamba_aligned has only GROUP_SIZE-1 = 2 layers)
    expected_tensors = [
        (NUM_BLOCKS, PAGE_SIZE_BYTES),
        (NUM_BLOCKS, PAGE_SIZE_BYTES),
        (NUM_BLOCKS, PAGE_SIZE_BYTES),
    ]

    # -- Expected group data refs (order matches kv_cache_groups) -------------
    ref = CanonicalKVCacheRef
    expected_group_refs = [
        # attn group: layers attn[0..2] → tensors 0,1,2 with full page size
        [
            ref(tensor_idx=0, page_size_bytes=PAGE_SIZE_BYTES),
            ref(tensor_idx=1, page_size_bytes=PAGE_SIZE_BYTES),
            ref(tensor_idx=2, page_size_bytes=PAGE_SIZE_BYTES),
        ],
        # mla group: layers mla[0..2] → tensors 0,1,2 with full page size
        [
            ref(tensor_idx=0, page_size_bytes=PAGE_SIZE_BYTES),
            ref(tensor_idx=1, page_size_bytes=PAGE_SIZE_BYTES),
            ref(tensor_idx=2, page_size_bytes=PAGE_SIZE_BYTES),
        ],
        # unaligned mamba group: layers [0..2] → tensors 0,1,2 with unaligned page
        [
            ref(tensor_idx=0, page_size_bytes=unaligned_mamba_page_size),
            ref(tensor_idx=1, page_size_bytes=unaligned_mamba_page_size),
            ref(tensor_idx=2, page_size_bytes=unaligned_mamba_page_size),
        ],
        # aligned mamba group: layers [0..1] → tensors 0,1 with full page size
        [
            ref(tensor_idx=0, page_size_bytes=PAGE_SIZE_BYTES),
            ref(tensor_idx=1, page_size_bytes=PAGE_SIZE_BYTES),
        ],
    ]

    # Verify block tensors
    assert len(canonical.tensors) == len(expected_tensors)
    for block_tensor, (exp_num_blocks, exp_page_size) in zip(
        canonical.tensors, expected_tensors
    ):
        tensor = block_tensor.tensor
        assert tensor.dtype == torch.int8
        assert tensor.shape == (exp_num_blocks, exp_page_size)
        assert block_tensor.page_size_bytes == exp_page_size

    # Verify group data refs
    assert len(canonical.group_data_refs) == len(expected_group_refs)
    for actual_refs, exp_refs in zip(canonical.group_data_refs, expected_group_refs):
        assert len(actual_refs) == len(exp_refs)
        for actual, expected in zip(actual_refs, exp_refs):
            assert actual.tensor_idx == expected.tensor_idx
            assert actual.page_size_bytes == expected.page_size_bytes