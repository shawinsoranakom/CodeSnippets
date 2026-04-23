def main(args):
    model_dir = args.model_dir
    if args.model_dir is None:
        if args.custom_mm_prompts:
            raise ValueError(
                "custom_mm_prompts requires mm based models"
                "default llama3.1-8b-instruct is not mm based"
                "please specify model_dir to give a mm based model"
            )
        model_dir = "meta-llama/Llama-3.1-8B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_dir)

    if args.custom_mm_prompts:
        prompts = llm_prompts = get_custom_mm_prompts(args.num_prompts)
    else:
        prompts = get_samples(args, tokenizer)
        if args.enable_multimodal_chat:
            llm_prompts = [p.prompt for p in prompts]
        else:
            # add_special_tokens is False to avoid adding bos twice
            # when using chat templates
            llm_prompts = [
                {
                    "prompt_token_ids": tokenizer.encode(
                        prompt.prompt, add_special_tokens=False
                    ),
                    "multi_modal_data": prompt.multi_modal_data,
                }
                for prompt in prompts
            ]
    if args.method == "eagle" or args.method == "eagle3":
        eagle_dir = args.eagle_dir
        if args.method == "eagle" and eagle_dir is None:
            eagle_dir = "yuhuili/EAGLE-LLaMA3.1-Instruct-8B"

        elif args.method == "eagle3" and eagle_dir is None:
            eagle_dir = "yuhuili/EAGLE3-LLaMA3.1-Instruct-8B"
        speculative_config = {
            "method": args.method,
            "model": eagle_dir,
            "num_speculative_tokens": args.num_spec_tokens,
            "disable_padded_drafter_batch": args.disable_padded_drafter_batch,
            "parallel_drafting": args.parallel_drafting,
        }
    elif args.method == "ngram":
        speculative_config = {
            "method": "ngram",
            "num_speculative_tokens": args.num_spec_tokens,
            "prompt_lookup_max": args.prompt_lookup_max,
            "prompt_lookup_min": args.prompt_lookup_min,
        }
    elif args.method == "draft_model":
        assert args.draft_model is not None and args.draft_model != ""
        speculative_config = {
            "method": args.method,
            "model": args.draft_model,
            "num_speculative_tokens": args.num_spec_tokens,
            "enforce_eager": args.enforce_eager,
            "max_model_len": args.max_model_len,
            "parallel_drafting": args.parallel_drafting,
        }
    elif args.method == "mtp":
        speculative_config = {
            "method": "mtp",
            "num_speculative_tokens": args.num_spec_tokens,
        }
    else:
        raise ValueError(f"unknown method: {args.method}")

    llm = LLM(
        model=model_dir,
        trust_remote_code=True,
        tensor_parallel_size=args.tp,
        enable_chunked_prefill=args.enable_chunked_prefill,
        enforce_eager=args.enforce_eager,
        gpu_memory_utilization=args.gpu_memory_utilization,
        speculative_config=speculative_config,
        disable_log_stats=False,
        max_model_len=args.max_model_len,
        limit_mm_per_prompt={"image": 5},
        disable_chunked_mm_input=True,
        max_num_seqs=args.max_num_seqs,
        allowed_local_media_path=args.allowed_local_media_path,
    )

    sampling_params = SamplingParams(temperature=args.temp, max_tokens=args.output_len)
    if args.backend == "openai-chat":
        outputs = llm.chat(llm_prompts, sampling_params=sampling_params)
    else:
        outputs = llm.generate(
            llm_prompts,
            sampling_params=sampling_params,
        )

    # print the generated text
    if args.print_output:
        for i, output in enumerate(outputs):
            print("-" * 50)
            if not args.custom_mm_prompts:
                print(f"prompt: {prompts[i].prompt}")
            else:
                print(f"prompt: {prompts[i]}")
            print(f"generated text: {output.outputs[0].text}")
            print("-" * 50)

    metrics = llm.get_metrics()

    total_num_output_tokens = sum(
        len(output.outputs[0].token_ids) for output in outputs
    )
    num_drafts = 0
    num_draft_tokens = 0
    num_accepted_tokens = 0
    acceptance_counts = [0] * args.num_spec_tokens
    for metric in metrics:
        if metric.name == "vllm:spec_decode_num_drafts":
            assert isinstance(metric, Counter)
            num_drafts += metric.value
        elif metric.name == "vllm:spec_decode_num_draft_tokens":
            assert isinstance(metric, Counter)
            num_draft_tokens += metric.value
        elif metric.name == "vllm:spec_decode_num_accepted_tokens":
            assert isinstance(metric, Counter)
            num_accepted_tokens += metric.value
        elif metric.name == "vllm:spec_decode_num_accepted_tokens_per_pos":
            assert isinstance(metric, Vector)
            for pos in range(len(metric.values)):
                acceptance_counts[pos] += metric.values[pos]

    print("-" * 50)
    print(f"total_num_output_tokens: {total_num_output_tokens}")
    print(f"num_drafts: {num_drafts}")
    print(f"num_draft_tokens: {num_draft_tokens}")
    print(f"num_accepted_tokens: {num_accepted_tokens}")
    acceptance_length = 1 + (num_accepted_tokens / num_drafts) if num_drafts > 0 else 1
    print(f"mean acceptance length: {acceptance_length:.2f}")
    print("-" * 50)

    # print acceptance at each token position
    for i in range(len(acceptance_counts)):
        acceptance_rate = acceptance_counts[i] / num_drafts if num_drafts > 0 else 0
        print(f"acceptance at token {i}: {acceptance_rate:.2f}")

    return acceptance_length