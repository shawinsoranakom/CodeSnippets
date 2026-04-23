def test_nixl_metadata_hybrid_ssm_block_ids():
    """Test NixlConnectorMetadata correctly stores block IDs for FA + SSM
    groups with different block counts (kernel mismatch active)."""
    from vllm.distributed.kv_transfer.kv_connector.v1.nixl.metadata import (
        NixlConnectorMetadata,
    )

    metadata = NixlConnectorMetadata()

    # FA: 8 kernel blocks (2 logical * ratio=4), SSM: 2 logical blocks
    fa_blocks = [0, 1, 2, 3, 4, 5, 6, 7]
    ssm_blocks = [0, 1]

    metadata.add_new_req_to_recv(
        request_id="test-req-hybrid",
        local_block_ids=(fa_blocks, ssm_blocks),
        kv_transfer_params={
            "remote_block_ids": ([10, 11, 12, 13, 14, 15, 16, 17], [20, 21]),
            "remote_engine_id": "remote-engine",
            "remote_request_id": "prefill-test-req-hybrid",
            "remote_host": "localhost",
            "remote_port": 1234,
            "tp_size": 1,
        },
    )

    assert "test-req-hybrid" in metadata.reqs_to_recv
    req_meta = metadata.reqs_to_recv["test-req-hybrid"]

    # Verify local block IDs: different lengths per group
    assert len(req_meta.local_block_ids) == 2
    assert list(req_meta.local_block_ids[0]) == fa_blocks
    assert list(req_meta.local_block_ids[1]) == ssm_blocks
    assert len(req_meta.local_block_ids[0]) != len(req_meta.local_block_ids[1])

    # Verify remote block IDs: same asymmetry preserved
    assert req_meta.remote is not None
    assert len(req_meta.remote.block_ids) == 2
    assert list(req_meta.remote.block_ids[0]) == [10, 11, 12, 13, 14, 15, 16, 17]
    assert list(req_meta.remote.block_ids[1]) == [20, 21]
    assert len(req_meta.remote.block_ids[0]) != len(req_meta.remote.block_ids[1])