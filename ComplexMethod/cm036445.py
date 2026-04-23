def _compare_caches(
    config_0: VllmConfig,
    config_1: VllmConfig,
    *,
    item_capacity: int = 8,
    hit_rate: float = 0.5,
    max_items_per_iter: int = 3,
    is_cached_calls_per_iter: int,
    n_iter: int = 100,
    seed: int = 0,
):
    cache_0_p0 = MULTIMODAL_REGISTRY.processor_cache_from_config(config_0)
    cache_0_p1 = MULTIMODAL_REGISTRY.engine_receiver_cache_from_config(config_0)
    cache_1_p0 = MULTIMODAL_REGISTRY.processor_cache_from_config(config_1)
    cache_1_p1 = MULTIMODAL_REGISTRY.engine_receiver_cache_from_config(config_1)

    cache_size_gb = max(
        config_0.model_config.multimodal_config.mm_processor_cache_gb,
        config_1.model_config.multimodal_config.mm_processor_cache_gb,
    )
    item_size_gb = int(cache_size_gb / item_capacity)

    rng = np.random.RandomState(seed)
    all_items = [
        _dummy_item({"key": item_size_gb}, rng=rng)
        for _ in range(int(item_capacity / hit_rate))
    ]
    all_hashes = [
        MultiModalHasher.hash_kwargs(item=item.get_data()) for item in all_items
    ]

    prompt_update = PromptInsertion("dummy", "target", "insertion").resolve(0)

    for it in range(n_iter):
        num_items_to_select = rng.randint(0, max_items_per_iter)
        item_idxs_to_select = rng.choice(len(all_items), num_items_to_select)

        selected_items = [all_items[idx] for idx in item_idxs_to_select]
        selected_hashes = [all_hashes[idx] for idx in item_idxs_to_select]

        if cache_0_p0 is None:
            cache_0_p0_out = selected_items
        else:
            for _ in range(is_cached_calls_per_iter):
                cache_0_p0.is_cached(selected_hashes)

            cache_0_p0_out = [
                item
                for item, _ in cache_0_p0.get_and_update(
                    [(item, [prompt_update]) for item in selected_items],
                    selected_hashes,
                )
            ]

        if cache_1_p0 is None:
            cache_1_p0_out = selected_items
        else:
            for _ in range(is_cached_calls_per_iter):
                cache_1_p0.is_cached(selected_hashes)

            cache_1_p0_out = [
                item
                for item, _ in cache_1_p0.get_and_update(
                    [(item, [prompt_update]) for item in selected_items],
                    selected_hashes,
                )
            ]

        if cache_0_p1 is None:
            cache_0_p1_out = cache_0_p0_out
        else:
            cache_0_p1_out = cache_0_p1.get_and_update(cache_0_p0_out, selected_hashes)

        if cache_1_p1 is None:
            cache_1_p1_out = cache_1_p0_out
        else:
            cache_1_p1_out = cache_1_p1.get_and_update(cache_1_p0_out, selected_hashes)

        assert cache_0_p1_out == cache_1_p1_out, f"Failed at {it=}"