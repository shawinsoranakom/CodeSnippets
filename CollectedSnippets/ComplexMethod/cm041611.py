def test_chatml_rendering():
    tokenizer: Processor = AutoTokenizer.from_pretrained("llamafactory/tiny-random-qwen3")
    renderer = Renderer(template="chatml", processor=tokenizer)

    hf_inputs = _get_input_ids(tokenizer.apply_chat_template(HF_MESSAGES[:-1], add_generation_prompt=True))
    v1_inputs = renderer.render_messages(V1_MESSAGES[:-1], is_generate=True)
    assert v1_inputs["input_ids"] == hf_inputs
    assert v1_inputs["attention_mask"] == [1] * len(hf_inputs)
    assert v1_inputs["labels"] == [-100] * len(hf_inputs)
    assert v1_inputs["loss_weights"] == [0.0] * len(hf_inputs)

    hf_inputs_part = _get_input_ids(tokenizer.apply_chat_template(HF_MESSAGES[:-1], add_generation_prompt=False))
    hf_inputs_full = _get_input_ids(tokenizer.apply_chat_template(HF_MESSAGES, add_generation_prompt=False))
    v1_inputs_full = renderer.render_messages(V1_MESSAGES, is_generate=False)
    assert v1_inputs_full["input_ids"] == hf_inputs_full
    assert v1_inputs_full["attention_mask"] == [1] * len(hf_inputs_full)
    assert v1_inputs_full["labels"] == [-100] * len(hf_inputs_part) + hf_inputs_full[len(hf_inputs_part) :]
    assert v1_inputs_full["loss_weights"] == [0.0] * len(hf_inputs_part) + [1.0] * (
        len(hf_inputs_full) - len(hf_inputs_part)
    )