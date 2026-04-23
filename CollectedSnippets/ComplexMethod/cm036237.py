def test_kv_cache_events_with_lora(blocks_to_cache: int):
    """Test BlockStored events contain correct lora_id when using LoRA requests."""
    block_size = 16
    num_blocks = blocks_to_cache + 1

    # Create KVCacheManager with events enabled
    manager = KVCacheManager(
        make_kv_cache_config(block_size, num_blocks),
        max_model_len=8192,
        enable_caching=True,
        enable_kv_cache_events=True,
        hash_block_size=block_size,
    )

    # Test with LoRA request
    lora_request = LoRARequest(
        lora_name="test_lora", lora_int_id=42, lora_path="/test/path"
    )

    num_tokens = block_size * blocks_to_cache
    req_with_lora = make_request(
        "lora_req",
        list(range(num_tokens)),
        block_size,
        sha256,
        lora_request=lora_request,
    )

    # Allocate slots and get events
    _ = manager.allocate_slots(req_with_lora, num_tokens)
    events = manager.take_events()

    # Verify BlockStored event contains correct lora_id
    block_stored_event = events[-1]
    assert isinstance(block_stored_event, BlockStored)
    assert block_stored_event.lora_id == 42  # Should match lora_request.adapter_id
    assert len(block_stored_event.block_hashes) == blocks_to_cache
    assert block_stored_event.block_size == block_size

    # Clean up
    manager.free(req_with_lora)

    # Test without LoRA request (should have lora_id=None)
    req_without_lora = make_request(
        "no_lora_req", list(range(num_tokens)), block_size, sha256
    )

    _ = manager.allocate_slots(req_without_lora, num_tokens)
    events = manager.take_events()

    block_stored_event = events[-1]
    assert isinstance(block_stored_event, BlockStored)
    assert block_stored_event.lora_id is None  # Should be None when no LoRA request
    assert len(block_stored_event.block_hashes) == blocks_to_cache
    assert block_stored_event.block_size == block_size