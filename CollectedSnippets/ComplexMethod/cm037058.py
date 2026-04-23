def get_pooling_config(
    model: str,
    revision: str | None = "main",
) -> dict[str, Any] | None:
    """
    This function gets the pooling and normalize
    config from the model - only applies to
    sentence-transformers models.

    Args:
        model: The name of the Hugging Face model.
        revision: The specific version of the model to use.
            Defaults to 'main'.

    Returns:
        A dictionary containing the pooling type and whether
            normalization is used, or None if no pooling configuration is found.
    """
    if is_remote_gguf(model):
        model, _ = split_remote_gguf(model)

    modules_file_name = "modules.json"

    modules_dict = None
    if file_or_path_exists(
        model=model, config_name=modules_file_name, revision=revision
    ):
        modules_dict = get_hf_file_to_dict(modules_file_name, model, revision)

    if modules_dict is None:
        return None

    logger.info("Found sentence-transformers modules configuration.")

    pooling = next(
        (
            item
            for item in modules_dict
            if item["type"] == "sentence_transformers.models.Pooling"
        ),
        None,
    )
    normalize = bool(
        next(
            (
                item
                for item in modules_dict
                if item["type"] == "sentence_transformers.models.Normalize"
            ),
            False,
        )
    )

    if pooling:
        from vllm.config.pooler import SEQ_POOLING_TYPES, TOK_POOLING_TYPES

        pooling_file_name = "{}/config.json".format(pooling["path"])
        pooling_dict = get_hf_file_to_dict(pooling_file_name, model, revision) or {}

        logger.info("Found pooling configuration.")

        config: dict[str, Any] = {"use_activation": normalize}
        for key, val in pooling_dict.items():
            if val is True:
                pooling_type = parse_pooling_type(key)
                if pooling_type in SEQ_POOLING_TYPES:
                    config["seq_pooling_type"] = pooling_type
                elif pooling_type in TOK_POOLING_TYPES:
                    config["tok_pooling_type"] = pooling_type
                else:
                    logger.debug("Skipping unrelated field: %r=%r", key, val)

        return config

    return None