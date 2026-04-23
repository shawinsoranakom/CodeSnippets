def test_worker_adapter_manager(
    default_vllm_config, dist_init, dummy_model_gate_up, device, tmp_path
):
    # Should remove every LoRA not specified in the request.
    lora_config = LoRAConfig(
        max_lora_rank=8, max_cpu_loras=4, max_loras=4, lora_dtype=DEFAULT_DTYPE
    )

    model_config = ModelConfig(max_model_len=16)
    vllm_config = VllmConfig(model_config=model_config, lora_config=lora_config)

    vllm_config.scheduler_config.max_num_seqs = 4
    vllm_config.scheduler_config.max_num_batched_tokens = 2

    worker_adapter_manager = WorkerLoRAManager(vllm_config, device, EMBEDDING_MODULES)
    worker_adapter_manager.vocab_size = dummy_model_gate_up.unpadded_vocab_size
    worker_adapter_manager.create_lora_manager(dummy_model_gate_up)

    dummy_lora_files = f"{tmp_path}/lora_adapter"
    os.makedirs(dummy_lora_files, exist_ok=True)
    create_peft_lora(
        dummy_model_gate_up,
        save_dir=dummy_lora_files,
        target_modules=["layer1.dense1", "dense2"],
        lora_dtype=DEFAULT_DTYPE,
    )

    mapping = LoRAMapping([], [])
    worker_adapter_manager.set_active_adapters(
        [LoRARequest("1", 1, dummy_lora_files), LoRARequest("2", 2, dummy_lora_files)],
        mapping,
    )
    assert worker_adapter_manager.list_adapters() == {1, 2}
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[0] == 1
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[1] == 2

    worker_adapter_manager.set_active_adapters(
        [
            LoRARequest("1", 1, dummy_lora_files),
            LoRARequest("3", 3, dummy_lora_files),
            LoRARequest("4", 4, dummy_lora_files),
        ],
        mapping,
    )
    assert worker_adapter_manager.list_adapters() == {1, 3, 4}
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[0] == 1
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[1] == 3
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[2] == 4

    worker_adapter_manager.set_active_adapters(
        [
            LoRARequest("1", 1, dummy_lora_files),
            LoRARequest("2", 2, dummy_lora_files),
            LoRARequest("5", 5, dummy_lora_files),
        ],
        mapping,
    )
    assert worker_adapter_manager.list_adapters() == {1, 2, 5}
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[0] == 1
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[1] == 2
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[2] == 5

    worker_adapter_manager.set_active_adapters(
        [
            LoRARequest("1", 1, dummy_lora_files),
            LoRARequest("1", 1, dummy_lora_files),
            LoRARequest("1", 1, dummy_lora_files),
        ],
        mapping,
    )
    assert worker_adapter_manager.list_adapters() == {1}
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[0] == 1
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[1] is None
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[2] is None

    worker_adapter_manager.set_active_adapters(
        [
            LoRARequest("6", 6, dummy_lora_files),
            LoRARequest("7", 7, dummy_lora_files),
            LoRARequest("8", 8, dummy_lora_files),
        ],
        mapping,
    )
    assert worker_adapter_manager.list_adapters() == {6, 7, 8}
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[0] == 8
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[1] == 6
    assert worker_adapter_manager._adapter_manager.lora_index_to_id[2] == 7

    # Over capacity
    with pytest.raises(RuntimeError):
        worker_adapter_manager.set_active_adapters(
            [
                LoRARequest("10", 10, dummy_lora_files),
                LoRARequest("11", 11, dummy_lora_files),
                LoRARequest("12", 12, dummy_lora_files),
                LoRARequest("13", 13, dummy_lora_files),
                LoRARequest("14", 14, dummy_lora_files),
            ],
            mapping,
        )

    assert worker_adapter_manager.device == device
    punica_wrapper = worker_adapter_manager._adapter_manager.punica_wrapper_mapping.get(
        DEFAULT_LANGUAGE_WRAPPER_KEY
    )
    assert punica_wrapper.device == device