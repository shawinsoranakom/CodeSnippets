def test_lora_model_manager(default_vllm_config, dist_init, dummy_model, device):
    model = dummy_model
    model_lora1 = create_lora(
        1, model, ["layer1.dense1", "dense2", "lm_head"], device=device
    )
    model_lora2 = create_lora(2, model, ["dense1", "dense2", "lm_head"], device=device)
    model_lora3 = create_lora(3, model, ["dense1", "dense2", "lm_head"], device=device)
    manager = LoRAModelManager(
        model,
        2,
        2,
        2,
        LoRAConfig(
            max_lora_rank=8, max_cpu_loras=3, max_loras=2, lora_dtype=DEFAULT_DTYPE
        ),
        device=device,
    )
    assert all(x is None for x in manager.lora_index_to_id)
    assert manager.add_adapter(model_lora1)
    assert manager.activate_adapter(1)
    assert manager.lora_index_to_id[0] == 1
    assert not manager.add_adapter(model_lora1)
    assert not manager.activate_adapter(1)
    assert manager.add_adapter(model_lora2)
    assert manager.activate_adapter(2)
    assert manager.lora_index_to_id[0] == 1
    assert manager.lora_index_to_id[1] == 2
    assert not manager.add_adapter(model_lora2)
    assert not manager.activate_adapter(2)
    assert manager.add_adapter(model_lora3)
    assert manager.lora_index_to_id[0] == 1
    assert manager.lora_index_to_id[1] == 2
    with pytest.raises(ValueError):
        assert manager.activate_adapter(3)
    assert manager.lora_index_to_id[0] == 1
    assert manager.lora_index_to_id[1] == 2
    assert manager.remove_adapter(model_lora2.id)
    assert manager.lora_index_to_id[1] is None
    assert not manager.remove_adapter(model_lora2.id)
    assert manager.remove_adapter(model_lora1.id)
    assert not manager.remove_adapter(model_lora1.id)
    assert manager.add_adapter(model_lora1)
    assert manager.lora_index_to_id[0] is None
    assert manager.lora_index_to_id[1] is None
    assert manager.add_adapter(model_lora2)
    assert manager.activate_adapter(3)
    assert manager.lora_index_to_id[0] == 3
    assert manager.lora_index_to_id[1] is None
    assert manager.activate_adapter(2)
    assert manager.lora_index_to_id[0] == 3
    assert manager.lora_index_to_id[1] == 2
    assert manager.device == device
    assert (
        manager.punica_wrapper_mapping.get(DEFAULT_LANGUAGE_WRAPPER_KEY).device
        == device
    )
    assert hasattr(manager, "supported_lora_modules")
    assert sorted(manager.supported_lora_modules) == [
        "dense1",
        "dense2",
        "lm_head",
        "output",
    ]