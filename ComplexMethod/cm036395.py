def test_compatibility_hash_validation(
    default_vllm_config,
    dist_init,
    mismatch_type,
    config_overrides,
    version_override,
    should_fail,
    enforce_handshake_compat,
):
    """
    Test NIXL compatibility hash validation during handshake.

    Parameters:
        mismatch_type: description of what is being tested
        config_overrides: dict of config to override for the remote instance
        version_override: version dict e.g. {"vllm_version": "0.6.1"}
        should_fail: whether the handshake should fail
        enforce_handshake_compat: whether to enforce compatibility checking
    """
    local_vllm_config = create_vllm_config(
        model="facebook/opt-125m",
        block_size=16,
        kv_connector_extra_config={
            "enforce_handshake_compat": enforce_handshake_compat
        },
    )
    kv_cache_config = make_kv_cache_config(block_size=16, num_blocks=2)
    decode_connector = NixlConnector(
        local_vllm_config, KVConnectorRole.WORKER, kv_cache_config
    )
    decode_worker = decode_connector.connector_worker
    kv_cache_spec = cast(
        AttentionSpec, kv_cache_config.kv_cache_groups[0].kv_cache_spec
    )
    kv_cache_shape = decode_worker.attn_backends[0].get_kv_cache_shape(
        num_blocks=kv_cache_config.num_blocks,
        block_size=kv_cache_spec.block_size,
        num_kv_heads=kv_cache_spec.num_kv_heads,
        head_size=kv_cache_spec.head_size,
    )
    shared_tensor = torch.zeros(*kv_cache_shape, dtype=kv_cache_spec.dtype)
    unique_tensor = torch.zeros(*kv_cache_shape, dtype=kv_cache_spec.dtype)
    # Build kv_caches from the actual layer names in kv_cache_config so that
    # _layer_specs lookups in register_kv_caches always find a matching key.
    layer_names = [
        name for group in kv_cache_config.kv_cache_groups for name in group.layer_names
    ]
    kv_caches = {
        name: shared_tensor if i % 2 == 0 else unique_tensor
        for i, name in enumerate(layer_names)
    }
    decode_connector.register_kv_caches(kv_caches)

    remote_config_params: dict[str, Any] = {
        "model": "facebook/opt-125m",
        "block_size": 16,
        **config_overrides,
    }
    remote_vllm_config = create_vllm_config(**remote_config_params)

    with contextlib.ExitStack() as stack:
        if "vllm_version" in version_override:
            stack.enter_context(
                patch("vllm.__version__", version_override["vllm_version"])
            )
        elif "connector_version" in version_override:
            stack.enter_context(
                patch.object(
                    nixl.metadata,
                    "NIXL_CONNECTOR_VERSION",
                    version_override["connector_version"],
                )
            )
        remote_hash = compute_nixl_compatibility_hash(
            remote_vllm_config,
            decode_worker.backend_name,
            decode_worker.transfer_topo.cross_layers_blocks,
        )

    prefill_block_size = config_overrides.get("block_size", 16)
    prefill_metadata = NixlAgentMetadata(
        engine_id=FakeNixlConnectorWorker.REMOTE_ENGINE_ID,
        agent_metadata=FakeNixlWrapper.AGENT_METADATA,
        kv_caches_base_addr=[0],
        device_id=0,
        num_blocks=1,
        block_lens=[4096 * prefill_block_size],  # slot_size * block_size
        kv_cache_layout="HND",
        block_size=prefill_block_size,
        ssm_sizes=(0, 0),
        attn_backend_name=decode_worker.backend_name,
    )
    handshake_payload = NixlHandshakePayload(
        compatibility_hash=remote_hash,
        agent_metadata_bytes=msgspec.msgpack.encode(prefill_metadata),
    )

    # Mock ZMQ socket to return our handshake payload
    mock_socket = MagicMock()
    mock_socket.recv.return_value = msgspec.msgpack.encode(handshake_payload)

    # Mock add_remote_agent to avoid actual NIXL operations
    # Patch zmq_ctx to return our mock socket
    with (
        patch.object(decode_worker, "add_remote_agent", return_value="fake_agent"),
        patch.object(nixl.worker, "zmq_ctx") as mock_zmq_ctx,
    ):
        mock_zmq_ctx.return_value.__enter__.return_value = mock_socket

        if should_fail:
            with pytest.raises(RuntimeError, match="compatibility hash mismatch"):
                decode_worker._nixl_handshake(
                    host="localhost",
                    port=1234,
                    remote_tp_size=1,
                    expected_engine_id=FakeNixlConnectorWorker.REMOTE_ENGINE_ID,
                )
        else:
            result = decode_worker._nixl_handshake(
                host="localhost",
                port=1234,
                remote_tp_size=1,
                expected_engine_id=FakeNixlConnectorWorker.REMOTE_ENGINE_ID,
            )
            # Verify handshake returned agent mapping
            assert isinstance(result, dict)
            assert len(result) == 1