def load_weights_using_from_2_way_softmax(
    model, weights: Iterable[tuple[str, torch.Tensor]]
):
    # refer to https://huggingface.co/Qwen/Qwen3-Reranker-0.6B/discussions/3
    from vllm.model_executor.layers.vocab_parallel_embedding import ParallelLMHead
    from vllm.model_executor.model_loader.weight_utils import default_weight_loader

    model_config = model.vllm_config.model_config
    hf_config = model.config
    text_config = hf_config.get_text_config()

    tokens = getattr(
        hf_config,
        "classifier_from_token",
        getattr(text_config, "classifier_from_token", []),
    )
    tokens = cast(list[int], tokens)
    assert len(tokens) == 2

    language_model = _get_language_model_for_seq_cls(model)
    is_vlm = language_model is not model
    using_vlm_head = is_vlm and hasattr(language_model, "score")

    language_model.lm_head = ParallelLMHead(
        text_config.vocab_size,
        text_config.hidden_size,
    )
    if text_config.tie_word_embeddings:
        # embed_tokens is the assumed name for input embeddings. If the model does not
        # have this attribute, we fall back to get_input_embeddings(), which is used by
        # the Transformers modeling backend.
        text_backbone = language_model.model
        embed_tokens = (
            text_backbone.embed_tokens
            if hasattr(text_backbone, "embed_tokens")
            else text_backbone.get_input_embeddings()
        )
        language_model.lm_head = language_model.lm_head.tie_weights(embed_tokens)

    with _disable_seq_cls_loading_on_inner_model(language_model, is_vlm):
        # ModelForPooling is dynamically defined inside the _create_pooling_model_cls
        # function, so we need use this hacky method to obtain it.
        pooling_model_cls = next(
            x for x in type(model).__mro__ if x.__name__ == "ModelForPooling"
        )
        loaded_weights = pooling_model_cls.load_weights(model, weights)

    from vllm.tokenizers import get_tokenizer

    tokenizer = get_tokenizer(
        model_config.tokenizer,
        revision=model_config.tokenizer_revision,
        tokenizer_mode=model_config.tokenizer_mode,
        trust_remote_code=model_config.trust_remote_code,
    )

    false_id = tokenizer.convert_tokens_to_ids(tokens[0])
    true_id = tokenizer.convert_tokens_to_ids(tokens[1])
    lm_head_weight = language_model.lm_head.weight
    score_weight = lm_head_weight.data[[true_id]].to(
        torch.float32
    ) - lm_head_weight.data[[false_id]].to(torch.float32)

    score_layer = language_model.score if using_vlm_head else model.score
    param = score_layer.weight
    weight_loader = getattr(param, "weight_loader", default_weight_loader)
    weight_loader(param, score_weight)

    del language_model.lm_head

    score_weight_name = (
        "language_model.score.weight" if using_vlm_head else "score.weight"
    )
    loaded_weights.add(score_weight_name)

    lm_head_name = "lm_head.weight"
    if hf_to_vllm_mapper := getattr(model, "hf_to_vllm_mapper", None):
        lm_head_name = hf_to_vllm_mapper._map_name(lm_head_name)
    loaded_weights.discard(lm_head_name)
    return loaded_weights