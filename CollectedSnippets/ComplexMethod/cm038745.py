def get_timing_stats_from_engine(llm_engine: LLMEngine) -> dict[str, dict[str, float]]:
    """
    Get all multimodal timing stats from the LLM engine.

    Collects both preprocessing stats (HF processor, hashing, cache lookup,
    prompt update) and encoder forward pass timing, merged by request_id.

    Args:
        llm_engine: The LLM engine (has input_processor and workers).

    Returns:
        Dictionary mapping request_id to merged stats dict containing
        both preprocessing and encoder timing metrics.

    Example:
        {
            'request-123': {
                'get_mm_hashes_secs': 0.02,
                'get_cache_missing_items_secs': 0.01,
                'apply_hf_processor_secs': 0.45,
                'merge_mm_kwargs_secs': 0.01,
                'apply_prompt_updates_secs': 0.03,
                'preprocessor_total_secs': 0.51,
                'encoder_forward_secs': 0.23,
                'num_encoder_calls': 1
            }
        }
    """
    observability_config = llm_engine.vllm_config.observability_config
    if not observability_config or not observability_config.enable_mm_processor_stats:
        return {}

    renderer = llm_engine.renderer
    mm_processor_stats = renderer._mm_timing_registry.stat()

    encoder_stats = dict[str, dict[str, float]]()
    for worker_stats in llm_engine.collective_rpc("get_encoder_timing_stats"):
        if not worker_stats:
            continue

        for request_id, stats_dict in worker_stats.items():
            if request_id not in encoder_stats:
                encoder_stats[request_id] = dict(stats_dict)
            else:
                # Aggregate timing metrics across workers
                current_time = encoder_stats[request_id].get(
                    "encoder_forward_secs", 0.0
                )
                new_time = stats_dict.get("encoder_forward_secs", 0.0)
                encoder_stats[request_id]["encoder_forward_secs"] = max(
                    current_time, new_time
                )

                current_calls = encoder_stats[request_id].get("num_encoder_calls", 0)
                new_calls = stats_dict.get("num_encoder_calls", 0)
                encoder_stats[request_id]["num_encoder_calls"] = max(
                    current_calls, new_calls
                )

    merged_stats = dict[str, dict[str, float]]()

    for request_id, prep_dict in mm_processor_stats.items():
        merged_stats[request_id] = dict(prep_dict)

    for request_id, enc_dict in encoder_stats.items():
        if request_id in merged_stats:
            merged_stats[request_id].update(enc_dict)
            continue

        # In V1 engine, the request_id in encoder_stats has a suffix
        # appended to the original request_id (which is used in
        # preprocessing_stats).
        # We try to strip the suffix to find the matching request.
        possible_original_id = request_id.rpartition("-")[0]
        if possible_original_id and possible_original_id in merged_stats:
            merged_stats[possible_original_id].update(enc_dict)
        else:
            merged_stats[request_id] = dict(enc_dict)

    return merged_stats