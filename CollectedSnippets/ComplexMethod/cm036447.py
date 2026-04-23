def _run_test_cache_eviction_shm(
    p0_cache: BaseMultiModalProcessorCache,
    p1_cache: BaseMultiModalReceiverCache,
    base_item_size: int,
):
    request1_hashes = ["image_A", "image_B", "image_C"]
    request1_items = {
        h: MultiModalKwargsItem.dummy(5 * base_item_size) for h in request1_hashes
    }
    request1_items_p0_result = []

    request2_hashes = ["image_G", "image_A"]
    request2_items = {
        h: MultiModalKwargsItem.dummy(
            (5 if h in request1_hashes else 2) * base_item_size
        )
        for h in request2_hashes
    }
    request2_items_p0_result = []

    request3_hashes = ["image_G", "image_H", "image_I", "image_B"]
    request3_items = {
        h: MultiModalKwargsItem.dummy(
            (5 if h in request1_hashes else 2) * base_item_size
        )
        for h in request3_hashes
    }
    request3_items_p0_result = []

    ##########################
    # STEP 1: Request 1 send
    # This will fill up the cache
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

        p0_result = p0_cache.get_and_update_item(item_tuple, h)
        # Only get mm item, ignore prompt update result
        request1_items_p0_result.append(p0_result[0])

    ###########################
    # Process request 1 for P1 Cache
    ###########################
    # Touch all mm hash for P1 Cache before process
    for mm_hash, mm_item in zip(request1_hashes, request1_items_p0_result):
        p1_cache.touch_receiver_cache_item(mm_hash, mm_item)

    for mm_hash, mm_item in zip(request1_hashes, request1_items_p0_result):
        p1_cache.get_and_update_item(mm_item, mm_hash)

    expected_hashes = ["image_A", "image_B", "image_C"]
    assert list(p0_cache._shm_cache.key_index.keys()) == expected_hashes

    ##########################
    # STEP 2: Request 2 send
    # There is no eviction because image_A is protected
    # No new item can add to cache
    ##########################
    sender_is_cached_item_req2 = p0_cache.is_cached(request2_hashes)
    assert sender_is_cached_item_req2 == [False, True]

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

        p0_result = p0_cache.get_and_update_item(item_tuple, h)
        # Only get mm item, ignore prompt update result
        request2_items_p0_result.append(p0_result[0])

    # image_A cannot be evict then
    # image_G will fail to allocate anyway and image_A still in cache
    assert p0_cache.is_cached(request2_hashes) == [False, True]

    ###########################
    # Process request 2 for P1 Cache
    ###########################

    # Touch all mm hash for P1 Cache before process
    for mm_hash, mm_item in zip(request2_hashes, request2_items_p0_result):
        p1_cache.touch_receiver_cache_item(mm_hash, mm_item)

    for mm_hash, mm_item in zip(request2_hashes, request2_items_p0_result):
        p1_cache.get_and_update_item(mm_item, mm_hash)

    # Prove that cache state is unchanged
    expected_hashes = ["image_A", "image_B", "image_C"]
    assert list(p0_cache._shm_cache.key_index.keys()) == expected_hashes

    ##########################
    # STEP 3: Request 3 send
    ##########################
    ##### Prove that cache eviction work normally
    sender_is_cached_item_req3 = p0_cache.is_cached(request3_hashes)
    assert sender_is_cached_item_req3 == [False, False, False, True]

    # Touch all mm hash for P0 Cache before process
    for mm_hash in request3_hashes:
        p0_cache.touch_sender_cache_item(mm_hash)

    ###########################
    # Process request 3 for P0 Cache
    ###########################
    for i, h in enumerate(request3_hashes):
        # Use precomputed cache state again
        is_cached = sender_is_cached_item_req3[i]
        item_tuple = (request3_items[h], []) if not is_cached else None
        print(f"Request 3: key={h} | cached={is_cached}")
        p0_result = p0_cache.get_and_update_item(item_tuple, h)
        # Only get mm item, ignore prompt update result
        request3_items_p0_result.append(p0_result[0])

    # image_A got evict and image_G add to cache
    # image_B is still protected
    # image_G, image_H fit but image_I cannot fit
    assert p0_cache.is_cached(request3_hashes) == [True, True, False, True]

    ###########################
    # Process request 3 for P1 Cache
    ###########################

    # Touch all mm hash for P1 Cache before process
    for mm_hash, mm_item in zip(request3_hashes, request3_items_p0_result):
        p1_cache.touch_receiver_cache_item(mm_hash, mm_item)

    for mm_hash, mm_item in zip(request3_hashes, request3_items_p0_result):
        p1_cache.get_and_update_item(mm_item, mm_hash)

    expected_hashes = ["image_B", "image_C", "image_G", "image_H"]
    assert list(p0_cache._shm_cache.key_index.keys()) == expected_hashes