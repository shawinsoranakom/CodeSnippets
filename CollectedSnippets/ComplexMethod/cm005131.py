def convert(
    checkpoint_path: str, config: Gemma3Config, variant: str
) -> tuple[dict[str, torch.Tensor], Sequence[np.ndarray] | None]:
    """Loads Orbax checkpoint from `input_path` and converts it to HF tree."""
    checkpointer = obc.PyTreeCheckpointer()
    ckpt = checkpointer.restore(checkpoint_path)
    hf_tree: dict[str, torch.Tensor] = {}
    orbax_tree_flat = tree.flatten_with_path(ckpt)

    def update_tree(path: str, weights: np.ndarray, target_dtype: torch.dtype) -> None:
        hf_tree[path] = torch.from_numpy(weights.astype("float32")).type(target_dtype)
        if _VERBOSE.value:
            logging.info(
                "%s converted shape=%s with dtype=%s",
                path,
                weights.shape,
                target_dtype,
            )

    for paths, value in orbax_tree_flat:
        if paths[0].startswith("SigLiPFromPatches_"):
            if not _INCLUDE_VISION_ENCODER.value:
                continue

            path, weights = convert_siglip_weight(config=config.vision_config, paths=paths, weights=value)
            update_tree(f"model.{path}", weights, config.vision_config.dtype)
        else:
            for path, weights in convert_transformer_weights(config=config.text_config, paths=paths, weights=value):
                if not _INCLUDE_VISION_ENCODER.value:
                    # Paths generated during weights conversion assume it is targeting a Gemma3ForConditionalGeneration
                    # model, which has a Gemma3TextModel at "model.language_model". If _INCLUDE_VISION_ENCODER.value is
                    # False, then this is targeting a Gemma3ForCausalLM, which has its Gemma3TextModel at "model", so
                    # the "language_model." portion of the path needs to be removed prior to calling load_state_dict().
                    path = path.replace("language_model.", "")

                if variant == _VARIANT_EMBEDDINGGEMMA:
                    # EmbeddingGemma only the Gemma3TextModel instead of an LLM of VLM class for loading weights, and
                    # defers final model construction to SentenceTransformers, so the "model." portion of the path
                    # needs to be removed prior to calling load_state_dict().
                    path = path[len("model.") :]

                update_tree(path, weights, config.text_config.dtype)

    if variant == _VARIANT_EMBEDDINGGEMMA:
        return hf_tree, [weight[1].T for weight in orbax_tree_flat[: _NUM_LINEAR_LAYERS.value]]

    if _INCLUDE_VISION_ENCODER.value:
        hf_tree["lm_head.weight"] = hf_tree["model.language_model.embed_tokens.weight"]
    else:
        hf_tree["lm_head.weight"] = hf_tree["model.embed_tokens.weight"]

    return hf_tree, None