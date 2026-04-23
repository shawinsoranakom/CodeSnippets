def main(args):
    model = args.model_type
    if model not in model_example_map:
        raise ValueError(f"Model type {model} is not supported.")

    if args.tensor_parallel_size is not None and args.tensor_parallel_size < 1:
        raise ValueError(
            f"tensor_parallel_size must be a positive integer, "
            f"got {args.tensor_parallel_size}"
        )

    modality = args.modality
    mm_input = get_multi_modal_input(args)
    data = mm_input["data"]
    questions = mm_input["questions"]

    req_data = model_example_map[model](questions, modality)

    # Disable other modalities to save memory
    default_limits = {"image": 0, "video": 0, "audio": 0, "vision_chunk": 0}
    req_data.engine_args.limit_mm_per_prompt = default_limits | dict(
        req_data.engine_args.limit_mm_per_prompt or {}
    )

    engine_args = req_data.engine_args
    engine_args.seed = args.seed
    mm_processor_cache_gb = 0 if args.disable_mm_processor_cache else 4
    engine_args.mm_processor_cache_gb = mm_processor_cache_gb
    if args.tensor_parallel_size is not None:
        engine_args.tensor_parallel_size = args.tensor_parallel_size
    llm = LLM.from_engine_args(engine_args)

    # Don't want to check the flag multiple times, so just hijack `prompts`.
    prompts = (
        req_data.prompts
        if args.use_different_prompt_per_request
        else [req_data.prompts[0]]
    )

    # We set temperature to 0.2 so that outputs can be different
    # even when all prompts are identical when running batch inference.
    sampling_params = (
        SamplingParams(
            temperature=0.2, max_tokens=64, stop_token_ids=req_data.stop_token_ids
        )
        if req_data.sampling_params is None
        else req_data.sampling_params
    )

    def _mm_data(data, modality):
        if modality == "image+video":
            return {"image": data["image"], "video": data["video"]}
        return {modality: data}

    def _mm_uuid(uuid, modality):
        if modality == "image+video":
            return {"image": uuid, "video": uuid + "v"}
        return {modality: uuid}

    def _mm_empty(modality):
        if modality == "image+video":
            return {"image": None, "video": None}
        return {modality: None}

    assert args.num_prompts > 0
    if args.num_prompts == 1:
        # Single inference
        uuid = "uuid_0"
        inputs = {
            "prompt": prompts[0],
            "multi_modal_data": _mm_data(data, modality),
            "multi_modal_uuids": _mm_uuid(uuid, modality),
        }
        inputs_with_empty_media = {
            "prompt": prompts[0],
            "multi_modal_data": _mm_empty(modality),
            "multi_modal_uuids": _mm_uuid(uuid, modality),
        }
    else:
        # Batch inference
        if args.image_repeat_prob is not None:
            if modality == "image+video":
                raise ValueError(
                    "--image-repeat-prob is not supported for 'image+video' modality"
                )
            # Repeat images with specified probability of "image_repeat_prob"
            inputs, inputs_with_empty_media = apply_image_repeat(
                args.image_repeat_prob,
                args.num_prompts,
                data,
                prompts,
                modality,
            )
        else:
            # Use the same image/video for all prompts
            inputs = []
            inputs_with_empty_media = []
            for i in range(args.num_prompts):
                uuid = "uuid_{}".format(i)
                inputs.append(
                    {
                        "prompt": prompts[i % len(prompts)],
                        "multi_modal_data": _mm_data(data, modality),
                        "multi_modal_uuids": _mm_uuid(uuid, modality),
                    }
                )
                inputs_with_empty_media.append(
                    {
                        "prompt": prompts[i % len(prompts)],
                        "multi_modal_data": _mm_empty(modality),
                        "multi_modal_uuids": _mm_uuid(uuid, modality),
                    }
                )

    # Add LoRA request if applicable
    lora_request = (
        req_data.lora_requests * args.num_prompts if req_data.lora_requests else None
    )

    with time_counter(args.time_generate):
        outputs = llm.generate(
            inputs,
            sampling_params=sampling_params,
            lora_request=lora_request,
        )

    print("-" * 50)
    for o in outputs:
        generated_text = o.outputs[0].text
        print(generated_text)
        print("-" * 50)

    if args.verify_mm_cache_hit_with_uuids:
        try:
            # Verify cache hits with UUIDs
            print(
                "Sending a second batch of requests with empty media"
                " and matching UUIDs."
            )
            outputs = llm.generate(
                inputs_with_empty_media,
                sampling_params=sampling_params,
                lora_request=lora_request,
            )
            print("-" * 50)
            for o in outputs:
                generated_text = o.outputs[0].text
                print(generated_text)
                print("-" * 50)
        except Exception as e:
            print(f"Failed to verify cache hits with UUIDs. Error: {e}")