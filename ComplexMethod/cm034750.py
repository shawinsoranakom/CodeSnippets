def get_inputs(messages: Messages, model_data: dict, model_type: str, do_continue: bool = False) -> str:
    if model_type in ("gpt2", "gpt_neo", "gemma", "gemma2"):
        inputs = format_prompt(messages, do_continue=do_continue)
    elif model_type == "mistral" and model_data.get("author")  == "mistralai":
        inputs = format_prompt_mistral(messages, do_continue)
    elif "config" in model_data and "tokenizer_config" in model_data["config"] and "eos_token" in model_data["config"]["tokenizer_config"]:
        eos_token = model_data["config"]["tokenizer_config"]["eos_token"]
        if eos_token in ("<|endoftext|>", "<eos>", "</s>"):
            inputs = format_prompt_custom(messages, eos_token, do_continue)
        elif eos_token == "<|im_end|>":
            inputs = format_prompt_qwen(messages, do_continue)
        elif "content" in eos_token and eos_token["content"] == "\u003C｜end▁of▁sentence｜\u003E":
            inputs = format_prompt_qwen2(messages, do_continue)
        elif eos_token == "<|eot_id|>":
            inputs = format_prompt_llama(messages, do_continue)
        else:
            inputs = format_prompt(messages, do_continue=do_continue)
    else:
        inputs = format_prompt(messages, do_continue=do_continue)
    return inputs