def test_lru_lora_model_manager(default_vllm_config, dist_init, dummy_model, device):
    # This tests just the LRU cache functionality, everything else is
    # tested in test_lora_model_manager
    model = dummy_model
    model_lora1 = create_lora(
        1, model, ["layer1.dense1", "dense2", "lm_head"], device=device
    )
    model_lora2 = create_lora(2, model, ["dense1", "dense2", "lm_head"], device=device)
    model_lora3 = create_lora(3, model, ["dense1", "dense2", "lm_head"], device=device)
    model_lora4 = create_lora(4, model, ["dense1", "dense2", "lm_head"], device=device)
    manager = LRUCacheLoRAModelManager(
        model,
        2,
        2,
        2,
        LoRAConfig(
            max_lora_rank=8, max_cpu_loras=2, max_loras=2, lora_dtype=DEFAULT_DTYPE
        ),
        device=device,
    )
    assert all(x is None for x in manager.lora_index_to_id)

    # Add up to capacity
    assert manager.add_adapter(model_lora1)
    assert manager.add_adapter(model_lora2)
    assert manager.activate_adapter(1)
    assert manager.activate_adapter(2)

    assert set(manager.list_adapters()) == {1, 2}
    assert manager.lora_index_to_id[0] == 1
    assert manager.lora_index_to_id[1] == 2

    # Add over capacity
    assert manager.add_adapter(model_lora3)
    assert manager.add_adapter(model_lora4)
    assert manager.activate_adapter(3)
    assert manager.activate_adapter(4)

    assert set(manager.list_adapters()) == {3, 4}
    assert manager.lora_index_to_id[0] == 3
    assert manager.lora_index_to_id[1] == 4

    # Add 3 again to move it to the top and then add 2
    # should return false since it's in already
    assert not manager.add_adapter(model_lora3)
    assert not manager.activate_adapter(3)
    assert manager.add_adapter(model_lora2)
    assert manager.activate_adapter(2)

    assert set(manager.list_adapters()) == {3, 2}
    assert manager.lora_index_to_id[0] == 3
    assert manager.lora_index_to_id[1] == 2

    # Remove manually
    assert manager.remove_adapter(3)
    assert not manager.remove_adapter(3)

    assert set(manager.list_adapters()) == {2}
    assert manager.lora_index_to_id[0] is None
    assert manager.lora_index_to_id[1] == 2

    assert manager.add_adapter(model_lora3)
    assert manager.activate_adapter(3)
    assert manager.add_adapter(model_lora4)
    assert manager.activate_adapter(4)

    assert set(manager.list_adapters()) == {3, 4}
    assert manager.lora_index_to_id[0] == 3
    assert manager.lora_index_to_id[1] == 4

    assert manager.remove_oldest_adapter()
    assert set(manager.list_adapters()) == {4}
    assert manager.lora_index_to_id[0] is None
    assert manager.lora_index_to_id[1] == 4

    assert manager.remove_oldest_adapter()
    assert set(manager.list_adapters()) == set()
    assert all(x is None for x in manager.lora_index_to_id)

    assert not manager.remove_oldest_adapter()
    assert set(manager.list_adapters()) == set()
    assert all(x is None for x in manager.lora_index_to_id)

    # pinning
    assert manager.add_adapter(model_lora3)
    assert manager.activate_adapter(3)
    assert manager.add_adapter(model_lora4)
    assert manager.activate_adapter(4)
    assert set(manager.list_adapters()) == {3, 4}
    with pytest.raises(ValueError):
        assert manager.pin_adapter(1)
    assert manager.pin_adapter(3)
    # Remove manually
    assert manager.remove_adapter(3)
    assert not manager.remove_adapter(3)

    assert set(manager.list_adapters()) == {4}
    assert manager.lora_index_to_id[0] is None
    assert manager.lora_index_to_id[1] == 4

    assert manager.add_adapter(model_lora1)
    assert manager.pin_adapter(1)
    assert manager.add_adapter(model_lora2)
    assert manager.activate_adapter(2)

    assert set(manager.list_adapters()) == {1, 2}
    assert manager.lora_index_to_id[0] == 1
    assert manager.lora_index_to_id[1] == 2

    assert manager.remove_oldest_adapter()
    assert set(manager.list_adapters()) == {1}
    assert manager.lora_index_to_id[0] == 1
    assert manager.lora_index_to_id[1] is None

    with pytest.raises(RuntimeError):
        assert manager.remove_oldest_adapter()

    assert set(manager.list_adapters()) == {1}
    assert (
        manager.punica_wrapper_mapping.get(DEFAULT_LANGUAGE_WRAPPER_KEY).device
        == device
    )
    assert manager.device == device