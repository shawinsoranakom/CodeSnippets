def load_mistral_tokenizer(data):
    if torch.is_tensor(data):
        data = data.numpy().tobytes()

    try:
        from transformers.integrations.mistral import MistralConverter
    except ModuleNotFoundError:
        from transformers.models.pixtral.convert_pixtral_weights_to_hf import MistralConverter

    mistral_vocab = json.loads(data)

    special_tokens = {}
    vocab = {}

    max_vocab = mistral_vocab["config"]["default_vocab_size"]
    max_vocab -= len(mistral_vocab["special_tokens"])

    for w in mistral_vocab["vocab"]:
        r = w["rank"]
        if r >= max_vocab:
            continue

        vocab[base64.b64decode(w["token_bytes"])] = r

    for w in mistral_vocab["special_tokens"]:
        if "token_bytes" in w:
            special_tokens[base64.b64decode(w["token_bytes"])] = w["rank"]
        else:
            special_tokens[w["token_str"]] = w["rank"]

    all_special = []
    for v in special_tokens:
        all_special.append(v)

    special_tokens.update(vocab)
    vocab = special_tokens
    return {"tokenizer_object": MistralConverter(vocab=vocab, additional_special_tokens=all_special).converted(), "legacy": False}