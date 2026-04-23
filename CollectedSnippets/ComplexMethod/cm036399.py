def test_multi_example_connector_consistency():
    """
    Tests that MultiConnector with two ExampleConnectors saves
    identical KV cache data to separate storage locations.
    """
    storage_1_path = Path("storage_1/")
    storage_2_path = Path("storage_2/")
    shutil.rmtree(storage_1_path, ignore_errors=True)
    shutil.rmtree(storage_2_path, ignore_errors=True)
    storage_1_path.mkdir()
    storage_2_path.mkdir()

    # Configure MultiConnector with two ExampleConnectors
    kv_transfer_config = KVTransferConfig(
        kv_connector="MultiConnector",
        kv_role="kv_both",
        kv_connector_extra_config={
            "connectors": [
                {
                    "kv_connector": "TestExampleConnector",
                    "kv_role": "kv_both",
                    "kv_connector_extra_config": {
                        "shared_storage_path": str(storage_1_path),
                        "name": "storage1",
                    },
                    "kv_connector_module_path": "tests.v1.kv_connector.unit.utils",
                },
                {
                    "kv_connector": "TestExampleConnector",
                    "kv_role": "kv_both",
                    "kv_connector_extra_config": {
                        "shared_storage_path": str(storage_2_path),
                        "name": "storage2",
                    },
                    "kv_connector_module_path": "tests.v1.kv_connector.unit.utils",
                },
            ]
        },
    )

    llm = LLM(
        model=MODEL_NAME,
        enforce_eager=True,
        gpu_memory_utilization=0.5,
        kv_transfer_config=kv_transfer_config,
    )
    # Run generation - this should trigger saving KV cache
    # Use a single prompt to avoid race conditions depending on the order of scheduling
    _ = llm.generate(PROMPTS[0], SAMPLING_PARAMS)

    # --- Verification ---

    # Check that both storage directories were populated
    local_subdirs = list(storage_1_path.iterdir())
    external_subdirs = list(storage_2_path.iterdir())

    assert len(local_subdirs) > 0, (
        f"Local storage path {storage_1_path} is empty after generation."
    )
    assert len(external_subdirs) > 0, (
        f"External storage path {storage_2_path} is empty after generation."
    )
    assert len(local_subdirs) == len(external_subdirs), (
        f"Mismatch in number of cache entries: "
        f"Local={len(local_subdirs)}, External={len(external_subdirs)}"
    )

    # The subdirectories should correspond to the prompt hashes
    # Since prompts are the same, the hash directories should be the same name
    local_subdir_names = sorted([d.name for d in local_subdirs])
    external_subdir_names = sorted([d.name for d in external_subdirs])
    assert local_subdir_names == external_subdir_names, (
        "Cache directory names do not match between local and external storage"
    )

    # Compare the contents of each corresponding cache directory
    for subdir_name in local_subdir_names:
        print(f"Comparing contents of cache directory: {subdir_name}")
        assert _compare_directories(
            storage_1_path / subdir_name, storage_2_path / subdir_name
        ), (
            f"Contents differ for cache directory '{subdir_name}' between "
            f"{storage_1_path} and {storage_2_path}"
        )

    events = get_connector_events()
    # First event is set_xfer_handshake_metadata from initialization, then
    # get_num_new_matched_tokens and update_state_after_alloc from generate().
    assert events["storage1-SCHEDULER"][:4] == [
        "set_xfer_handshake_metadata",
        "get_num_new_matched_tokens 0",
        "update_state_after_alloc num_blocks=[0] 0",
        "build_connector_meta",
    ]
    # First three events are from initialization (register_kv_caches,
    # set_host_xfer_buffer_ops, get_handshake_metadata), then generate() events.
    assert events["storage1-WORKER"][:8] == [
        "register_kv_caches",
        "set_host_xfer_buffer_ops",
        "get_handshake_metadata",
        "handle_preemptions",
        "bind_connector_metadata",
        "start_load_kv",
        "wait_for_layer_load",
        "save_kv_layer",
    ]
    assert events["storage2-SCHEDULER"][:4] == [
        "set_xfer_handshake_metadata",
        "get_num_new_matched_tokens 0",
        "update_state_after_alloc num_blocks=[0] 0",
        "build_connector_meta",
    ]
    assert events["storage2-WORKER"][:8] == [
        "register_kv_caches",
        "set_host_xfer_buffer_ops",
        "get_handshake_metadata",
        "handle_preemptions",
        "bind_connector_metadata",
        "start_load_kv",
        "wait_for_layer_load",
        "save_kv_layer",
    ]

    # Reset prefix cache or else we'll just get the tokens back from there.
    llm.reset_prefix_cache()

    # Run generation again - this should trigger loading from the first
    # connector.
    _ = llm.generate(PROMPTS[1], SAMPLING_PARAMS)

    events = get_connector_events()
    # get_num_new_matched_tokens will return new tokens from the first
    # connector so update_state_after_alloc will be with allocated blocks
    # on that one but with zero blocks for others (first nonzero match is
    # chosen).
    assert events["storage1-SCHEDULER"][:3] == [
        "get_num_new_matched_tokens 0",
        "update_state_after_alloc num_blocks=[7] 96",
        "build_connector_meta",
    ]
    assert events["storage2-SCHEDULER"][:3] == [
        "get_num_new_matched_tokens 0",
        "update_state_after_alloc num_blocks=[0] 0",
        "build_connector_meta",
    ]

    # Delete storage1 connector state
    shutil.rmtree(storage_1_path)

    # Reset prefix cache or else we'll just get the tokens back from there.
    llm.reset_prefix_cache()

    # Run generation again - this should trigger loading from the first
    # connector.
    _ = llm.generate(PROMPTS[0], SAMPLING_PARAMS)

    events = get_connector_events()
    # get_num_new_matched_tokens will be called for both connectors but will
    # return 0 from the first connector, but the second connector should have
    # a hit, so update_state_after_alloc will only be called with allocated
    # blocks for the second connector.
    assert events["storage1-SCHEDULER"][:3] == [
        "get_num_new_matched_tokens 0",
        "update_state_after_alloc num_blocks=[0] 0",
        "build_connector_meta",
    ]
    assert events["storage2-SCHEDULER"][:3] == [
        "get_num_new_matched_tokens 0",
        "update_state_after_alloc num_blocks=[7] 96",
        "build_connector_meta",
    ]

    # Clean up
    shutil.rmtree(storage_1_path)
    shutil.rmtree(storage_2_path)