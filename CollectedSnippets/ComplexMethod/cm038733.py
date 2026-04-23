def run_hf(
    requests: list[SampleRequest],
    model: str,
    tokenizer: TokenizerLike,
    n: int,
    max_batch_size: int,
    trust_remote_code: bool,
    disable_detokenize: bool = False,
    dtype: torch.dtype | None = torch.float16,
    enable_torch_compile: bool = False,
) -> float:
    assert isinstance(tokenizer, PreTrainedTokenizerBase), (
        "the hf backend only supports HF tokenizers"
    )
    llm = AutoModelForCausalLM.from_pretrained(
        model, dtype=dtype, trust_remote_code=trust_remote_code
    )
    if llm.config.model_type == "llama":
        # To enable padding in the HF backend.
        tokenizer.pad_token = tokenizer.eos_token
    llm = llm.to(current_platform.device_type)
    if enable_torch_compile:
        llm = torch.compile(llm)

    pbar = tqdm(total=len(requests))
    start = time.perf_counter()
    batch: list[str] = []
    max_prompt_len = 0
    max_output_len = 0
    for i in range(len(requests)):
        prompt = requests[i].prompt
        prompt_len = requests[i].prompt_len
        output_len = requests[i].expected_output_len
        # Add the prompt to the batch.
        batch.append(prompt)
        max_prompt_len = max(max_prompt_len, prompt_len)
        max_output_len = max(max_output_len, output_len)
        if len(batch) < max_batch_size and i != len(requests) - 1:
            # Check if we can add more requests to the batch.
            next_prompt_len = requests[i + 1].prompt_len
            next_output_len = requests[i + 1].expected_output_len
            if (
                max(max_prompt_len, next_prompt_len)
                + max(max_output_len, next_output_len)
            ) <= 2048:
                # We can add more requests to the batch.
                continue

        # Generate the sequences.
        input_ids = tokenizer(batch, return_tensors="pt", padding=True).input_ids
        llm_outputs = llm.generate(
            input_ids=input_ids.to(current_platform.device_type),
            do_sample=True,
            num_return_sequences=n,
            temperature=1.0,
            top_p=1.0,
            use_cache=True,
            max_new_tokens=max_output_len,
        )
        if not disable_detokenize:
            # Include the decoding time.
            tokenizer.batch_decode(llm_outputs, skip_special_tokens=True)
        pbar.update(len(batch))

        # Clear the batch.
        batch = []
        max_prompt_len = 0
        max_output_len = 0
    end = time.perf_counter()
    return end - start