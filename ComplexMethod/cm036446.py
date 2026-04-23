def _run_test_cache_eviction_lru(
    p0_cache: BaseMultiModalProcessorCache,
    p1_cache: BaseMultiModalReceiverCache,
    base_item_size: int,
):
    request1_hashes = [
        "image_A",
        "image_B",
        "image_C",
    ]
    request1_items = {
        h: MultiModalKwargsItem.dummy(nbytes=2 * base_item_size)
        for h in request1_hashes
    }

    request2_hashes = ["image_D", "image_E", "image_A", "image_C"]
    request2_items = {
        h: MultiModalKwargsItem.dummy(nbytes=1 * base_item_size)
        for h in request2_hashes
    }

    ##########################
    # STEP 1: Request 1 send
    ##########################
    sender_is_cached_item_req1 = p0_cache.is_cached(request1_hashes)
    # Cache is empty
    assert sender_is_cached_item_req1 == [False, False, False]

    # Touch all mm hash for P0 Cache before process
    for mm_hash in request1_hashes:
        p0_cache.touch_sender_cache_item(mm_hash)

    ###########################
    # Process request 1 for P0 Cache
    ###########################
    item_tuple: MultiModalProcessorCacheInItem
    for i, h in enumerate(request1_hashes):
        # Use precomputed cache state
        is_cached = sender_is_cached_item_req1[i]
        item_tuple = (request1_items[h], []) if not is_cached else None
        print(f"Request 1: key={h} | cached={is_cached}")

        p0_cache.get_and_update_item(item_tuple, h)

    ###########################
    # Process request 1 for P1 Cache
    ###########################
    # Touch all mm hash for P1 Cache before process
    for mm_hash in request1_hashes:
        p1_cache.touch_receiver_cache_item(mm_hash)

    for h in request1_hashes:
        p1_cache.get_and_update_item(request1_items[h], h)

    expected_hashes = ["image_A", "image_B", "image_C"]
    assert list(p0_cache._cache.order) == expected_hashes

    ##########################
    # STEP 2: Request 2 send
    ##########################
    sender_is_cached_item_req2 = p0_cache.is_cached(request2_hashes)
    assert sender_is_cached_item_req2 == [False, False, True, True]

    # Touch all mm hash for P0 Cache before process
    for mm_hash in request2_hashes:
        p0_cache.touch_sender_cache_item(mm_hash)

    ###########################
    # Process request 2 for P0 Cache
    ###########################
    for i, h in enumerate(request2_hashes):
        # Use precomputed cache state again
        is_cached = sender_is_cached_item_req2[i]
        item_tuple = (request2_items[h], []) if not is_cached else None
        print(f"Request 2: key={h} | cached={is_cached}")

        p0_cache.get_and_update_item(item_tuple, h)

    ###########################
    # Process request 2 for P1 Cache
    ###########################

    # Touch all mm hash for P1 Cache before process
    for mm_hash in request2_hashes:
        p1_cache.touch_receiver_cache_item(mm_hash)

    for h in request2_hashes:
        p1_cache.get_and_update_item(request2_items[h], h)

    expected_hashes = ["image_D", "image_E", "image_A", "image_C"]
    assert list(p0_cache._cache.order) == expected_hashes