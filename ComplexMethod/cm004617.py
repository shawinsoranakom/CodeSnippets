def extract_adapters_data(input_dir: str, output_dir: str):
    """Extract adapters data from the state dict and save weights and configs."""
    speech_lora = {}
    vision_lora = {}
    shards = [file for file in os.listdir(input_dir) if file.endswith(".safetensors")]
    for shard_file in shards:
        original_state_dict = load_file(os.path.join(input_dir, shard_file))
        for k, v in original_state_dict.items():
            if "lora" in k:
                if "speech" in k:
                    speech_lora[k.replace("speech.", "")] = v
                elif "vision" in k:
                    vision_lora[k.replace("vision.", "")] = v

    # Create and save the lora configs
    speech_lora_config = LoraConfig(
        r=320,
        lora_alpha=640,
        target_modules=r"model.layers.\d+.((self_attn.(qkv|o)_proj)|(mlp.(gate_up|down)_proj))",
        lora_dropout=0.01,
        task_type="CAUSAL_LM",
    )
    speech_lora_config.save_pretrained(os.path.join(output_dir, "speech-lora"))
    vision_lora_config = LoraConfig(
        r=256,
        lora_alpha=512,
        target_modules=r"model.layers.\d+.((self_attn.(qkv|o)_proj)|(mlp.(gate_up|down)_proj))",
        lora_dropout=0.0,
        task_type="CAUSAL_LM",
    )
    vision_lora_config.save_pretrained(os.path.join(output_dir, "vision-lora"))

    save_file(speech_lora, os.path.join(output_dir, "speech-lora", "adapter_model.safetensors"))
    save_file(vision_lora, os.path.join(output_dir, "vision-lora", "adapter_model.safetensors"))