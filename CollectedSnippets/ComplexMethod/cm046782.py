def auto_select_gpu_ids(
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
) -> tuple[Optional[list[int]], Dict[str, Any]]:
    metadata: Dict[str, Any] = {"selection_mode": "auto"}

    if get_device() != DeviceType.CUDA:
        metadata["selection_mode"] = "non_cuda"
        return None, metadata

    required_gb, estimate_metadata = estimate_required_model_memory_gb(
        model_name,
        hf_token = hf_token,
        training_type = training_type,
        load_in_4bit = load_in_4bit,
        batch_size = batch_size,
        max_seq_length = max_seq_length,
        lora_rank = lora_rank,
        target_modules = target_modules,
        gradient_checkpointing = gradient_checkpointing,
        optimizer = optimizer,
    )
    metadata.update(estimate_metadata)
    parent_visible_spec = _get_parent_visible_gpu_spec()
    metadata["parent_cuda_visible_devices"] = parent_visible_spec["raw"]

    if not parent_visible_spec["supports_explicit_gpu_ids"]:
        metadata["selection_mode"] = "inherit_parent_visible"
        metadata["selected_gpu_ids"] = None
        return None, metadata

    if required_gb is None:
        # Cannot estimate model size -- fall back to all visible GPUs
        # rather than risk loading on a single GPU that may not have
        # enough memory.
        parent_ids = get_parent_visible_gpu_ids()
        metadata["selection_mode"] = "fallback_all"
        metadata["selected_gpu_ids"] = parent_ids
        return parent_ids, metadata

    utilization = get_visible_gpu_utilization()
    devices = utilization.get("devices", [])
    parent_ids = get_parent_visible_gpu_ids()

    if not devices:
        metadata["selection_mode"] = "fallback_all"
        metadata["selected_gpu_ids"] = parent_ids
        return parent_ids, metadata

    gpu_candidates = []
    for device in devices:
        total_gb = device.get("vram_total_gb")
        used_gb = device.get("vram_used_gb")
        if total_gb is None or used_gb is None:
            continue
        free_gb = max(total_gb - used_gb, 0.0)
        gpu_candidates.append(
            {
                "index": device["index"],
                "free_gb": free_gb,
            }
        )

    if not gpu_candidates:
        metadata["selection_mode"] = "fallback_all"
        metadata["selected_gpu_ids"] = parent_ids
        return parent_ids, metadata

    ranked = sorted(gpu_candidates, key = lambda item: (-item["free_gb"], item["index"]))
    free_by_index = {item["index"]: item["free_gb"] for item in ranked}
    selected: list[int] = []
    usable_gb = 0.0
    # Multi-GPU sharding has overhead from inter-GPU communication (NCCL
    # all-reduce, PCIe/NVLink transfers, synchronization barriers), so each
    # additional GPU contributes less than its raw free memory. The first GPU
    # keeps its full capacity (no cross-device overhead). 0.85 was calibrated
    # empirically on 2-8 GPU setups with NVLink and PCIe topologies -- the
    # 15% discount accounts for NCCL buffers (~2-5% of VRAM), pipeline bubble
    # overhead, and memory fragmentation from non-uniform shard sizes.
    multi_gpu_overhead = 0.85

    # Per-GPU check: activations don't shard, so each GPU needs its weight
    # shard + full activation cost. Use precomputed min_per_gpu_N values.
    vram_breakdown = estimate_metadata.get("vram_breakdown", {})

    for candidate in ranked:
        selected.append(candidate["index"])
        if len(selected) == 1:
            usable_gb = candidate["free_gb"]
        else:
            first_gpu_id = selected[0]
            usable_gb = free_by_index[first_gpu_id] + sum(
                free_by_index[gpu_id] * multi_gpu_overhead for gpu_id in selected[1:]
            )

        total_fits = usable_gb >= required_gb

        per_gpu_fits = True
        if total_fits and len(selected) > 1:
            min_key = f"min_per_gpu_{len(selected)}"
            min_per_gpu_gb = vram_breakdown.get(min_key)
            if min_per_gpu_gb is not None:
                smallest_free = min(free_by_index[gpu_id] for gpu_id in selected)
                per_gpu_fits = smallest_free >= min_per_gpu_gb

        if total_fits and per_gpu_fits:
            metadata["usable_gb"] = round(usable_gb, 3)
            metadata["selection_mode"] = "auto"
            metadata["selected_gpu_ids"] = selected
            logger.debug(
                "Selected GPUs automatically",
                model_name = model_name,
                selected_gpu_ids = selected,
                usable_gb = metadata["usable_gb"],
                required_gb = metadata.get("required_gb"),
                multi_gpu_overhead = multi_gpu_overhead,
            )
            return selected, metadata

    # Use only GPUs with verified VRAM data (from gpu_candidates, not raw devices)
    fallback_all = (
        [c["index"] for c in gpu_candidates] if gpu_candidates else parent_ids
    )
    metadata["selection_mode"] = "fallback_all"
    if ranked:
        fallback_usable = ranked[0]["free_gb"] + sum(
            c["free_gb"] * multi_gpu_overhead for c in ranked[1:]
        )
    else:
        fallback_usable = 0.0
    metadata["usable_gb"] = round(fallback_usable, 3)
    metadata["selected_gpu_ids"] = fallback_all
    logger.warning(
        "Falling back to all visible GPUs -- model may not fit",
        model_name = model_name,
        selected_gpu_ids = fallback_all,
        usable_gb = metadata["usable_gb"],
        required_gb = metadata.get("required_gb"),
        multi_gpu_overhead = multi_gpu_overhead,
    )
    return fallback_all, metadata