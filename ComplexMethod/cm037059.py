def get_sentence_transformer_tokenizer_config(
    model: str | Path, revision: str | None = "main"
) -> dict[str, Any] | None:
    """
    Returns the tokenization configuration dictionary for a
    given Sentence Transformer BERT model.

    Parameters:
    - model (str|Path): The name of the Sentence Transformer
    BERT model.
    - revision (str, optional): The revision of the m
    odel to use. Defaults to 'main'.

    Returns:
    - dict: A dictionary containing the configuration parameters
    for the Sentence Transformer BERT model.
    """
    sentence_transformer_config_files = [
        "sentence_bert_config.json",
        "sentence_roberta_config.json",
        "sentence_distilbert_config.json",
        "sentence_camembert_config.json",
        "sentence_albert_config.json",
        "sentence_xlm-roberta_config.json",
        "sentence_xlnet_config.json",
    ]
    encoder_dict = None

    for config_file in sentence_transformer_config_files:
        if (
            try_get_local_file(model=model, file_name=config_file, revision=revision)
            is not None
        ):
            encoder_dict = get_hf_file_to_dict(config_file, model, revision)
            if encoder_dict:
                break

    if not encoder_dict and not Path(model).is_absolute():
        try:
            # If model is on HuggingfaceHub, get the repo files
            repo_files = list_repo_files(model, revision=revision)
        except Exception:
            repo_files = []

        for config_name in sentence_transformer_config_files:
            if config_name in repo_files:
                encoder_dict = get_hf_file_to_dict(config_name, model, revision)
                if encoder_dict:
                    break

    if not encoder_dict:
        return None

    logger.info("Found sentence-transformers tokenize configuration.")

    if all(k in encoder_dict for k in ("max_seq_length", "do_lower_case")):
        return encoder_dict
    return None