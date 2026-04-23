def test_register_kv_caches():
    """Tests the memory registration logic with the underlying Mooncake engine."""

    vllm_config = create_vllm_config(
        kv_connector="MooncakeConnector", kv_role="kv_consumer"
    )

    with (
        set_current_vllm_config(vllm_config),
        patch_worker_dependencies(),
        patch(
            "vllm.distributed.kv_transfer.kv_connector.v1.mooncake.mooncake_connector.threading.Event"
        ),
        patch(
            "vllm.distributed.kv_transfer.kv_connector.v1.mooncake.mooncake_connector.threading.Thread"
        ) as mock_thread,
    ):
        connector = MooncakeConnector(vllm_config, KVConnectorRole.WORKER)
        worker = connector.connector_worker
        mock_thread.return_value.is_alive.return_value = False

        kv_cache_shape = FlashAttentionBackend.get_kv_cache_shape(
            num_blocks=2, block_size=16, num_kv_heads=4, head_size=64
        )
        tensor1 = torch.zeros(*kv_cache_shape, dtype=torch.float16)
        tensor2 = torch.zeros(*kv_cache_shape, dtype=torch.float16)
        kv_caches = {"layer0": tensor1, "layer1": tensor2}

        with patch.object(
            worker.engine, "batch_register_memory", return_value=0
        ) as mock_batch_register:
            connector.register_kv_caches(kv_caches)

            mock_batch_register.assert_called_once()
            registered_ptrs, registered_lens = mock_batch_register.call_args[0]
            expected_ptrs = {
                tensor.data_ptr()
                for kv_pair in kv_caches.values()
                for tensor in kv_pair
            }
            assert set(registered_ptrs) == expected_ptrs
            assert set(registered_lens) == {tensor1[0].nbytes}

            # Verify block_len_per_layer is set correctly.
            assert len(worker.block_len_per_layer) == len(registered_ptrs)
            for bl in worker.block_len_per_layer:
                assert bl == tensor1[0].nbytes // tensor1.shape[1]