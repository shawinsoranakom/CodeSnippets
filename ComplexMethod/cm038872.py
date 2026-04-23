def run_internvl(questions: list[str], modality: str) -> ModelRequestData:
    model_name = "OpenGVLab/InternVL3-2B"

    mm_limit = {"image": 1, "video": 1} if modality == "image+video" else {modality: 1}
    engine_args = EngineArgs(
        model=model_name,
        trust_remote_code=True,
        max_model_len=8192,
        limit_mm_per_prompt=mm_limit,
    )

    image_placeholder = "<image>"
    video_placeholder = "<video>"

    if modality == "image":
        placeholder = image_placeholder
    elif modality == "video":
        placeholder = video_placeholder
    elif modality == "image+video":
        placeholder = image_placeholder + "\n" + video_placeholder

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    messages = [
        [{"role": "user", "content": f"{placeholder}\n{question}"}]
        for question in questions
    ]
    prompts = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    # Stop tokens for InternVL
    # models variants may have different stop tokens
    # please refer to the model card for the correct "stop words":
    # https://huggingface.co/OpenGVLab/InternVL2-2B/blob/main/conversation.py
    stop_tokens = ["<|endoftext|>", "<|im_start|>", "<|im_end|>", "<|end|>"]
    stop_token_ids = [tokenizer.convert_tokens_to_ids(i) for i in stop_tokens]
    stop_token_ids = [token_id for token_id in stop_token_ids if token_id is not None]

    return ModelRequestData(
        engine_args=engine_args,
        prompts=prompts,
        stop_token_ids=stop_token_ids,
    )