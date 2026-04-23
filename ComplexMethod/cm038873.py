def run_minicpmv_base(questions: list[str], modality: str, model_name):
    assert modality in ["image", "video", "image+video"]
    # If you want to use `MiniCPM-o-2_6` with audio inputs, check `audio_language.py` # noqa

    # 2.0
    # The official repo doesn't work yet, so we need to use a fork for now
    # For more details, please see: See: https://github.com/vllm-project/vllm/pull/4087#issuecomment-2250397630 # noqa
    # model_name = "HwwwH/MiniCPM-V-2"

    # 2.5
    # model_name = "openbmb/MiniCPM-Llama3-V-2_5"

    # 2.6
    # model_name = "openbmb/MiniCPM-V-2_6"
    # o2.6

    # modality supports
    # 2.0: image
    # 2.5: image
    # 2.6: image, video
    # o2.6: image, video, audio
    # model_name = "openbmb/MiniCPM-o-2_6"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    mm_limit = {"image": 1, "video": 1} if modality == "image+video" else {modality: 1}
    engine_args = EngineArgs(
        model=model_name,
        max_model_len=4096,
        max_num_seqs=2,
        trust_remote_code=True,
        limit_mm_per_prompt=mm_limit,
    )
    # NOTE The stop_token_ids are different for various versions of MiniCPM-V
    # 2.0
    # stop_token_ids = [tokenizer.eos_id]

    # 2.5
    # stop_token_ids = [tokenizer.eos_id, tokenizer.eot_id]

    # 2.6 / o2.6
    stop_tokens = ["<|im_end|>", "<|endoftext|>"]
    stop_token_ids = [tokenizer.convert_tokens_to_ids(i) for i in stop_tokens]

    image_placeholder = "(<image>./</image>)"
    video_placeholder = "(<video>./</video>)"

    if modality == "image":
        placeholder = image_placeholder
    elif modality == "video":
        placeholder = video_placeholder
    elif modality == "image+video":
        placeholder = image_placeholder + "\n" + video_placeholder

    prompts = [
        tokenizer.apply_chat_template(
            [
                {
                    "role": "user",
                    "content": f"{placeholder}\n{question}",
                }
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        for question in questions
    ]

    return ModelRequestData(
        engine_args=engine_args,
        prompts=prompts,
        stop_token_ids=stop_token_ids,
    )