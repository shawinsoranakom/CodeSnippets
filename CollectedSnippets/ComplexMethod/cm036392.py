def test_register_kv_caches(
    default_vllm_config, dist_init, attn_backend, enable_cross_layers
):
    """
    Test that register_kv_caches() properly calls nixl_wrapper methods with
    correct data.

    This test verifies:
    1. nixl_wrapper.get_reg_descs() is called with caches_data containing
       tensor metadata
    2. nixl_wrapper.get_xfer_descs() is called with blocks_data containing
       block layout info
    """

    vllm_config = create_vllm_config(attention_backend=attn_backend)

    # Enable cross layers blocks
    vllm_config.kv_transfer_config.kv_connector_extra_config[
        "enable_cross_layers_blocks"
    ] = enable_cross_layers
    set_kv_cache_layout("HND")

    # Import the appropriate backend based on the parameter
    if attn_backend == "FLASH_ATTN":
        from vllm.v1.attention.backends.flash_attn import FlashAttentionBackend

        backend_cls = FlashAttentionBackend
    elif attn_backend == "ROCM_ATTN":
        from vllm.v1.attention.backends.rocm_attn import RocmAttentionBackend

        backend_cls = RocmAttentionBackend
    else:  # TRITON_ATTN
        from vllm.v1.attention.backends.triton_attn import TritonAttentionBackend

        backend_cls = TritonAttentionBackend

    nixl_worker = "vllm.distributed.kv_transfer.kv_connector.v1.nixl.worker"
    nixl_connector = "vllm.distributed.kv_transfer.kv_connector.v1.nixl.connector"
    with (
        patch(f"{nixl_worker}.NixlWrapper") as mock_nixl_wrapper,
        patch(f"{nixl_worker}.threading.Event"),
        patch(f"{nixl_worker}.threading.Thread") as mock_thread,
        patch(f"{nixl_connector}.get_current_attn_backend") as mock_get_attn_backend,
        patch(f"{nixl_worker}.get_current_attn_backends") as mock_get_attn_backends,
    ):
        # Ensure get_attn_backend returns the correct value due to
        # _cached_get_attn_backend returning the backend from previous
        # test run if not mocking.
        mock_get_attn_backend.return_value = backend_cls
        mock_get_attn_backends.return_value = [backend_cls]
        num_layers = 32
        block_size = 16
        num_blocks = 8
        num_heads = 4
        head_size = 16

        # TODO (NickLucche) the fact that connector depends on kv_cache_config for init
        # but cross-layer preference cant be inferred prior to creating kv_cache_config
        # is a bit awkward.
        dummy_connector = NixlConnector(
            vllm_config,
            KVConnectorRole.WORKER,
            make_kv_cache_config(block_size=block_size),
        )
        kv_cache_spec = FullAttentionSpec(
            block_size=block_size,
            num_kv_heads=num_heads,
            head_size=head_size,
            dtype=torch.float16,
        )
        if dummy_connector.prefer_cross_layer_blocks:
            kv_cache_config = KVCacheConfig(
                num_blocks=num_blocks,
                kv_cache_tensors=[
                    KVCacheTensor(
                        size=kv_cache_spec.page_size_bytes * num_blocks,
                        shared_by=["all-layers"],
                    )
                    for _ in range(num_layers)
                ],
                kv_cache_groups=[KVCacheGroupSpec(["all-layers"], kv_cache_spec)],
            )
        else:
            kv_cache_config = KVCacheConfig(
                num_blocks=num_blocks,
                kv_cache_tensors=[],
                kv_cache_groups=[
                    KVCacheGroupSpec(["layer0", "layer1", "layer2"], kv_cache_spec)
                ],
            )
        # Create connector
        connector = NixlConnector(vllm_config, KVConnectorRole.WORKER, kv_cache_config)
        connector.connector_worker = FakeNixlConnectorWorker(
            vllm_config,
            connector.engine_id,
            hand_shake_latency=0,
            kv_cache_config=kv_cache_config,
        )

        # Get the mock instance
        mock_wrapper_instance = mock_nixl_wrapper.return_value
        connector.connector_worker.nixl_wrapper = mock_wrapper_instance

        # Appease NixlHandshakePayload encoding with some bytes
        mock_wrapper_instance.get_agent_metadata.return_value = b"fake_agent_metadata"

        # Reassure the shutdown() check that the thread is terminated
        mock_thread.return_value.is_alive.return_value = False

        expected_tensor_size: int
        expected_base_addrs: list[int]
        expected_num_entries: int
        kv_caches: dict[str, torch.Tensor]
        if str(enable_cross_layers).lower() == "true":
            assert connector.prefer_cross_layer_blocks == (
                attn_backend in ("FLASH_ATTN", "FLASHINFER", "TRITON_ATTN")
            )
        else:
            assert not connector.prefer_cross_layer_blocks

        test_shape = backend_cls.get_kv_cache_shape(
            num_blocks=1, block_size=16, num_kv_heads=1, head_size=1
        )
        is_blocks_first = len(test_shape) == 5 and test_shape[0] == 1

        if connector.prefer_cross_layer_blocks:
            with set_current_vllm_config(vllm_config):
                _, cross_layers_kv_cache, _ = (
                    KVConnectorModelRunnerMixin.allocate_uniform_kv_caches(
                        kv_cache_config=kv_cache_config,
                        attn_groups=[
                            [
                                AttentionGroup(
                                    backend=backend_cls,
                                    layer_names=[],
                                    kv_cache_spec=kv_cache_spec,
                                    kv_cache_group_id=0,
                                )
                            ]
                        ],
                        cache_dtype="bfloat16",
                        device=torch.accelerator.current_device_index(),
                        kernel_block_sizes=[block_size],
                    )
                )
            # Store tensor info for validation
            expected_tensor_size = (
                cross_layers_kv_cache.element_size() * cross_layers_kv_cache.numel()
            )
            expected_base_addrs = [
                cross_layers_kv_cache.data_ptr(),
            ]
            expected_num_entries = 1

            expected_blocks_count = num_blocks * (2 if is_blocks_first else 1)

            kv_caches = {"all-layers": cross_layers_kv_cache}
        else:
            # Create test kv cache tensors using proper backend shape
            kv_cache_shape = backend_cls.get_kv_cache_shape(
                num_blocks=kv_cache_config.num_blocks,
                block_size=kv_cache_spec.block_size,
                num_kv_heads=kv_cache_spec.num_kv_heads,
                head_size=kv_cache_spec.head_size,
            )
            shared_tensor = torch.zeros(*kv_cache_shape, dtype=kv_cache_spec.dtype)
            unique_tensor = torch.zeros(*kv_cache_shape, dtype=kv_cache_spec.dtype)
            kv_caches = {
                "layer0": shared_tensor,
                "layer1": unique_tensor,
                "layer2": shared_tensor,
            }

            # Store tensor info for validation
            if is_blocks_first:
                expected_tensor_size = (
                    shared_tensor.element_size() * shared_tensor.numel()
                )
                expected_base_addrs = [
                    shared_tensor.data_ptr(),
                    unique_tensor.data_ptr(),
                ]
                expected_num_entries = 2
            else:
                expected_tensor_size = (
                    shared_tensor[0].element_size() * shared_tensor[0].numel()
                )
                expected_base_addrs = [
                    shared_tensor[0].data_ptr(),
                    shared_tensor[1].data_ptr(),
                    unique_tensor[0].data_ptr(),
                    unique_tensor[1].data_ptr(),
                ]
                expected_num_entries = 4
            expected_blocks_count = kv_cache_config.num_blocks * 4

        # Execute register_kv_caches
        connector.register_kv_caches(kv_caches)

        # Verify get_reg_descs was called with caches_data
        assert mock_wrapper_instance.get_reg_descs.called
        caches_data, _ = mock_wrapper_instance.get_reg_descs.call_args[0]
        assert len(caches_data) == expected_num_entries

        for i, cache_entry in enumerate(caches_data):
            base_addr, size, _tp_rank, _ = cache_entry
            assert size == expected_tensor_size, (
                f"Entry {i}: Expected tensor size {expected_tensor_size}, got {size}"
            )
            assert base_addr == expected_base_addrs[i], (
                f"Entry {i}: Expected base address {expected_base_addrs[i]}, "
                f"got {base_addr}"
            )

        # Verify get_xfer_descs was called with blocks_data
        assert mock_wrapper_instance.get_xfer_descs.called
        blocks_data, _ = mock_wrapper_instance.get_xfer_descs.call_args[0]

        # Validate blocks_data structure and size
        assert len(blocks_data) == expected_blocks_count, (
            f"Expected {expected_blocks_count} blocks, got {len(blocks_data)}"
        )

        if connector.prefer_cross_layer_blocks:
            num_blocks = 8
        else:
            num_blocks = kv_cache_config.num_blocks

        if is_blocks_first:
            expected_block_len = expected_tensor_size // num_blocks // 2
        else:
            expected_block_len = expected_tensor_size // num_blocks

        for i, block_entry in enumerate(blocks_data):
            block_start_addr, block_len, tp_rank = block_entry
            assert block_len == expected_block_len, (
                f"Block entry {i}: Expected block len {expected_block_len}, "
                f"got {block_len}"
            )

        assert connector.connector_worker.block_size == 16