def do_sample(
    llm: vllm.LLM,
    lora_path: str,
    lora_id: int,
    tensorizer_config_dict: dict | None = None,
) -> list[str]:
    prompts = [
        PROMPT_TEMPLATE.format(context="How many candidates are there?"),
        PROMPT_TEMPLATE.format(context="Count the number of candidates."),
        PROMPT_TEMPLATE.format(
            context="Which poll resource provided the most number of candidate information?"  # noqa: E501
        ),
        PROMPT_TEMPLATE.format(
            context="Return the poll resource associated with the most candidates."
        ),
    ]

    sampling_params = vllm.SamplingParams(
        temperature=0, max_tokens=64, stop=["<|im_end|>"]
    )
    if tensorizer_config_dict is not None:
        outputs = llm.generate(
            prompts,
            sampling_params,
            lora_request=LoRARequest(
                str(lora_id),
                lora_id,
                lora_path,
                tensorizer_config_dict=tensorizer_config_dict,
            )
            if lora_id
            else None,
        )
    else:
        outputs = llm.generate(
            prompts,
            sampling_params,
            lora_request=LoRARequest(str(lora_id), lora_id, lora_path)
            if lora_id
            else None,
        )
    lora_request = LoRARequest(str(lora_id), lora_id, lora_path) if lora_id else None
    generated_texts: list[str] = []
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        # The output should include  correct lora_request info
        if lora_request is not None:
            assert output.lora_request.lora_name == lora_request.lora_name
            assert output.lora_request.lora_int_id == lora_request.lora_int_id
            assert output.lora_request.lora_path == lora_request.lora_path
        else:
            assert output.lora_request is None
        generated_texts.append(generated_text)
        print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
    return generated_texts