def inference(
    text,
    text_lang,
    ref_audio_path,
    aux_ref_audio_paths,
    prompt_text,
    prompt_lang,
    top_k,
    top_p,
    temperature,
    text_split_method,
    batch_size,
    speed_factor,
    ref_text_free,
    split_bucket,
    fragment_interval,
    seed,
    keep_random,
    parallel_infer,
    repetition_penalty,
    sample_steps,
    super_sampling,
):
    seed = -1 if keep_random else seed
    actual_seed = seed if seed not in [-1, "", None] else random.randint(0, 2**32 - 1)
    inputs = {
        "text": text,
        "text_lang": dict_language[text_lang],
        "ref_audio_path": ref_audio_path,
        "aux_ref_audio_paths": [item.name for item in aux_ref_audio_paths] if aux_ref_audio_paths is not None else [],
        "prompt_text": prompt_text if not ref_text_free else "",
        "prompt_lang": dict_language[prompt_lang],
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "text_split_method": cut_method[text_split_method],
        "batch_size": int(batch_size),
        "speed_factor": float(speed_factor),
        "split_bucket": split_bucket,
        "return_fragment": False,
        "fragment_interval": fragment_interval,
        "seed": actual_seed,
        "parallel_infer": parallel_infer,
        "repetition_penalty": repetition_penalty,
        "sample_steps": int(sample_steps),
        "super_sampling": super_sampling,
    }
    try:
        for item in tts_pipeline.run(inputs):
            yield item, actual_seed
    except NO_PROMPT_ERROR:
        gr.Warning(i18n("V3不支持无参考文本模式，请填写参考文本！"))