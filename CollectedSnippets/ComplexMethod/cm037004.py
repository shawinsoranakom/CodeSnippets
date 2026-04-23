def test_packed_loras(default_vllm_config, dist_init, dummy_model_gate_up, device):
    model = dummy_model_gate_up
    model_lora = create_packed_lora(
        1,
        model,
        module_name="gate_up_proj",
        replaced_module_names=["gate_proj", "up_proj"],
        device=device,
    )
    model_lora1 = create_packed_lora(
        2,
        model,
        module_name="gate_up_proj",
        replaced_module_names=["gate_proj", "up_proj"],
        device=device,
        empty_replaced_module_name="gate_proj",
    )

    manager = LoRAModelManager(
        model,
        2,
        2,
        2,
        LoRAConfig(
            max_lora_rank=8, max_cpu_loras=2, max_loras=2, lora_dtype=DEFAULT_DTYPE
        ),
        device=device,
    )
    model = manager.model

    assert isinstance(
        model.get_submodule("gate_up_proj"), MergedColumnParallelLinearWithLoRA
    )
    # Verify packed lora is correct
    model_lora_clone = model_lora.clone(1)
    model_lora_clone1 = model_lora1.clone(1)
    assert manager.add_adapter(model_lora)
    assert manager.add_adapter(model_lora1)

    assert model_lora.get_lora("gate_proj") is None
    assert model_lora.get_lora("up_proj") is None
    assert model_lora1.get_lora("up_proj") is None
    packed_lora = model_lora.get_lora("gate_up_proj")
    assert packed_lora and isinstance(packed_lora, PackedLoRALayerWeights)

    torch.testing.assert_close(
        packed_lora.lora_a[0], model_lora_clone.get_lora("gate_proj").lora_a
    )
    torch.testing.assert_close(
        packed_lora.lora_b[0], model_lora_clone.get_lora("gate_proj").lora_b
    )
    torch.testing.assert_close(
        packed_lora.lora_a[1], model_lora_clone.get_lora("up_proj").lora_a
    )
    torch.testing.assert_close(
        packed_lora.lora_b[1], model_lora_clone.get_lora("up_proj").lora_b
    )

    packed_lora1 = model_lora1.get_lora("gate_up_proj")
    assert packed_lora1 and isinstance(packed_lora1, PackedLoRALayerWeights)

    assert packed_lora1.lora_a[0] is None
    assert packed_lora1.lora_b[0] is None
    torch.testing.assert_close(
        packed_lora1.lora_a[1], model_lora_clone1.get_lora("up_proj").lora_a
    )
    torch.testing.assert_close(
        packed_lora1.lora_b[1], model_lora_clone1.get_lora("up_proj").lora_b
    )