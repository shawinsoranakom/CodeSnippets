def estimate_required_model_memory_gb(
    model_name: str,
    *,
    hf_token: Optional[str] = None,
    training_type: Optional[str] = None,
    load_in_4bit: bool = True,
    batch_size: int = 4,
    max_seq_length: int = 2048,
    lora_rank: int = 16,
    target_modules: Optional[list] = None,
    gradient_checkpointing: str = "unsloth",
    optimizer: str = "adamw_8bit",
) -> tuple[Optional[float], Dict[str, Any]]:
    from .vram_estimation import (
        TrainingVramConfig,
        extract_arch_config,
        estimate_training_vram,
        CUDA_OVERHEAD_BYTES,
        QUANT_4BIT_FACTOR,
        DEFAULT_TARGET_MODULES,
    )

    model_size_bytes, source = estimate_fp16_model_size_bytes(
        model_name, hf_token = hf_token
    )
    metadata: Dict[str, Any] = {
        "mode": "inference" if training_type is None else "training",
        "model_size_source": source,
    }
    if model_size_bytes is None:
        metadata["required_gb"] = None
        return None, metadata

    model_size_gb = model_size_bytes / (1024**3)
    metadata["model_size_gb"] = round(model_size_gb, 3)
    min_buffer_gb = 2.0

    if training_type is None:
        if load_in_4bit:
            base_4bit_gb = model_size_gb / QUANT_4BIT_FACTOR
            required_gb = base_4bit_gb + max(base_4bit_gb * 0.3, min_buffer_gb)
        else:
            required_gb = model_size_gb * 1.3
        metadata["required_gb"] = round(required_gb, 3)
        return required_gb, metadata

    training_method = (
        "full"
        if training_type == "Full Finetuning"
        else ("qlora" if load_in_4bit else "lora")
    )
    vram_config = TrainingVramConfig(
        training_method = training_method,
        batch_size = batch_size,
        max_seq_length = max_seq_length,
        lora_rank = lora_rank,
        target_modules = target_modules or list(DEFAULT_TARGET_MODULES),
        gradient_checkpointing = gradient_checkpointing,
        optimizer = optimizer,
        load_in_4bit = load_in_4bit,
    )

    estimate_model = _resolve_model_identifier_for_gpu_estimate(
        model_name, hf_token = hf_token
    )
    config = _load_config_for_gpu_estimate(estimate_model, hf_token = hf_token)
    arch = extract_arch_config(config) if config is not None else None

    if arch is not None:
        breakdown = estimate_training_vram(arch, vram_config)
        required_gb = breakdown.total / (1024**3)
        metadata["required_gb"] = round(required_gb, 3)
        metadata["estimation_mode"] = "detailed"
        metadata["vram_breakdown"] = breakdown.to_gb_dict()
        max_gpus = max(1, get_visible_gpu_count())
        for n_gpus in range(1, max_gpus + 1):
            metadata["vram_breakdown"][f"min_per_gpu_{n_gpus}"] = round(
                breakdown.min_gpu_vram(n_gpus) / (1024**3), 3
            )
        return required_gb, metadata

    # Fallback when model config is unavailable
    overhead_gb = CUDA_OVERHEAD_BYTES / (1024**3)
    if training_method == "full":
        required_gb = model_size_gb * 3.5 + overhead_gb
    elif training_method == "qlora":
        base_4bit_gb = model_size_gb / QUANT_4BIT_FACTOR
        lora_overhead_gb = model_size_gb * 0.04
        act_gb = model_size_gb * 0.15 * (batch_size / 4) * (max_seq_length / 2048)
        required_gb = base_4bit_gb + lora_overhead_gb + act_gb + overhead_gb
    else:
        lora_overhead_gb = model_size_gb * 0.04
        act_gb = model_size_gb * 0.15 * (batch_size / 4) * (max_seq_length / 2048)
        required_gb = model_size_gb + lora_overhead_gb + act_gb + overhead_gb

    metadata["required_gb"] = round(required_gb, 3)
    metadata["estimation_mode"] = "fallback"
    return required_gb, metadata