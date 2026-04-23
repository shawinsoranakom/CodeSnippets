def main(args):
    model = args.model_type
    if model not in model_example_map:
        raise ValueError(f"Model type {model} is not supported.")

    if model == "funaudiochat" and not args.model:
        raise ValueError("--model is required when --model-type=funaudiochat")

    if args.tensor_parallel_size is not None and args.tensor_parallel_size < 1:
        raise ValueError(
            f"tensor_parallel_size must be a positive integer, "
            f"got {args.tensor_parallel_size}"
        )

    audio_count = args.num_audios
    req_data = model_example_map[model](
        question_per_audio_count[audio_count], audio_count
    )
    if model == "funaudiochat":
        req_data.engine_args.model = args.model

    # Disable other modalities to save memory
    default_limits = {"image": 0, "video": 0, "audio": 0}
    req_data.engine_args.limit_mm_per_prompt = default_limits | dict(
        req_data.engine_args.limit_mm_per_prompt or {}
    )

    engine_args = vars(req_data.engine_args) | {"seed": args.seed}
    if args.tensor_parallel_size is not None:
        engine_args["tensor_parallel_size"] = args.tensor_parallel_size
    llm = LLM(**engine_args)

    # We set temperature to 0.2 so that outputs can be different
    # even when all prompts are identical when running batch inference.
    sampling_params = SamplingParams(
        temperature=0.2, max_tokens=64, stop_token_ids=req_data.stop_token_ids
    )

    def get_input(start, end):
        mm_data = req_data.multi_modal_data
        if not mm_data:
            mm_data = {}
            if end - start > 0:
                mm_data = {
                    "audio": [
                        asset.audio_and_sample_rate for asset in audio_assets[start:end]
                    ]
                }

        inputs = {"multi_modal_data": mm_data}

        if req_data.prompt:
            inputs["prompt"] = req_data.prompt
        else:
            inputs["prompt_token_ids"] = req_data.prompt_token_ids

        return inputs

    # Batch inference
    assert args.num_prompts > 0
    if audio_count != 1:
        inputs = get_input(0, audio_count)
        inputs = [inputs] * args.num_prompts
    else:
        # For single audio input, we need to vary the audio input
        # to avoid deduplication in vLLM engine.
        inputs = []
        for i in range(args.num_prompts):
            start = i % len(audio_assets)
            inp = get_input(start, start + 1)
            inputs.append(inp)

    # Add LoRA request if applicable
    lora_request = (
        req_data.lora_requests * args.num_prompts if req_data.lora_requests else None
    )

    outputs = llm.generate(
        inputs,
        sampling_params=sampling_params,
        lora_request=lora_request,
    )

    for o in outputs:
        generated_text = o.outputs[0].text
        print(generated_text)