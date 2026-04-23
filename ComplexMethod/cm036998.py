def test_from_lora_tensors(qwen3_lora_files, device):
    tensors = load_file(os.path.join(qwen3_lora_files, "adapter_model.safetensors"))

    peft_helper = PEFTHelper.from_local_dir(
        qwen3_lora_files, max_position_embeddings=4096
    )
    lora_model = LoRAModel.from_lora_tensors(
        1,
        tensors,
        peft_helper=peft_helper,
        device=device,
    )
    for module_name, lora in lora_model.loras.items():
        assert lora.module_name == module_name
        assert lora.rank == 8
        assert lora.lora_alpha == 32
        assert lora.lora_a is not None
        assert lora.lora_b is not None
        assert lora.lora_a.device == torch.device(device)
        assert lora.lora_b.device == torch.device(device)
        assert lora.lora_a.shape[0] == lora.lora_b.shape[1], (
            f"{lora.lora_a.shape=}, {lora.lora_b.shape=}"
        )
        assert lora.lora_a.shape[0] == 8