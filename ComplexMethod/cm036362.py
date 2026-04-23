def test_nixl_metadata_hma_block_ids_structure():
    """
    Test that NixlConnectorMetadata correctly stores block IDs for multiple
    KV cache groups when HMA is enabled.
    """
    from vllm.distributed.kv_transfer.kv_connector.v1.nixl.metadata import (
        NixlConnectorMetadata,
    )

    metadata = NixlConnectorMetadata()

    # Add request with block IDs for 2 groups (FA + SW)
    fa_blocks = [0, 1, 2, 3, 4, 5, 6, 7]  # 8 blocks for FA
    sw_blocks = [8, 9, 10, 11]  # 4 blocks for SW (clipped)

    metadata.add_new_req_to_recv(
        request_id="test-req-hma",
        local_block_ids=(fa_blocks, sw_blocks),
        kv_transfer_params={
            "remote_block_ids": ([10, 11, 12, 13, 14, 15, 16, 17], [18, 19, 20, 21]),
            "remote_engine_id": "remote-engine",
            "remote_request_id": "prefill-test-req-hma",
            "remote_host": "localhost",
            "remote_port": 1234,
            "tp_size": 1,
        },
    )

    assert "test-req-hma" in metadata.reqs_to_recv
    req_meta = metadata.reqs_to_recv["test-req-hma"]

    # Verify local block IDs structure
    assert len(req_meta.local_block_ids) == 2
    assert list(req_meta.local_block_ids[0]) == fa_blocks
    assert list(req_meta.local_block_ids[1]) == sw_blocks

    # Verify remote block IDs structure
    assert req_meta.remote is not None
    assert len(req_meta.remote.block_ids) == 2
    assert list(req_meta.remote.block_ids[0]) == [10, 11, 12, 13, 14, 15, 16, 17]
    assert list(req_meta.remote.block_ids[1]) == [18, 19, 20, 21]