def test_multimodal_collator():
    model_args, data_args, *_ = get_infer_args(
        {"model_name_or_path": "Qwen/Qwen2-VL-2B-Instruct", "template": "qwen2_vl"}
    )
    tokenizer_module = load_tokenizer(model_args)
    template = get_template_and_fix_tokenizer(tokenizer_module["tokenizer"], data_args)
    config = AutoConfig.from_pretrained(model_args.model_name_or_path)
    with torch.device("meta"):
        model = AutoModelForImageTextToText.from_config(config)

    data_collator = MultiModalDataCollatorForSeq2Seq(
        template=template,
        model=model,
        pad_to_multiple_of=4,
        label_pad_token_id=IGNORE_INDEX,
        **tokenizer_module,
    )
    p = tokenizer_module["tokenizer"].pad_token_id
    q = IGNORE_INDEX
    s = tokenizer_module["tokenizer"].convert_tokens_to_ids("<|vision_start|>")
    e = tokenizer_module["tokenizer"].convert_tokens_to_ids("<|vision_end|>")
    m = tokenizer_module["tokenizer"].convert_tokens_to_ids("<|image_pad|>")
    fake_image = Image.new("RGB", (64, 64), (255, 255, 255))

    features = [
        {
            "input_ids": [0, 1, 2, 3],
            "attention_mask": [1, 1, 1, 1],
            "labels": [0, 1, 2, 3],
        },
    ]
    batch_input = data_collator(features)
    expected_input = {
        "input_ids": [
            [0, 1, 2, 3, s, m, m, m, m, e, p, p],
        ],
        "attention_mask": [
            [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        "labels": [
            [0, 1, 2, 3, q, q, q, q, q, q, q, q],
        ],
        "position_ids": [[[0, 1, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0]]] * 3,
        "rope_deltas": [[0]],
        **tokenizer_module["processor"].image_processor(fake_image),
    }
    if not is_transformers_version_greater_than("5.0.0"):
        # adapt position_ids and rope_deltas for transformers < 5.0.0
        # https://github.com/huggingface/transformers/pull/43972
        expected_input["position_ids"] = [[[0, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1]]] * 3
        expected_input["rope_deltas"] = [[-8]]

    assert batch_input.keys() == expected_input.keys()
    for k in batch_input.keys():
        if k == "position_ids" and batch_input[k].dim() == 3 and batch_input[k].shape[0] == 4:
            batch_input[k] = batch_input[k][1:]

        assert batch_input[k].eq(torch.tensor(expected_input[k])).all()