def convert(checkpoint_path: str, config: Gemma3nConfig) -> dict[str, torch.Tensor]:
    """Loads Orbax checkpoint from `input_path` and converts it to HF tree."""
    checkpointer = obc.PyTreeCheckpointer()
    ckpt = checkpointer.restore(checkpoint_path)
    hf_tree: dict[str, torch.Tensor] = {}

    def update_tree(path: str, weights: np.ndarray, target_dtype: torch.dtype) -> None:
        hf_tree[path] = torch.from_numpy(weights.astype("float32")).type(target_dtype)
        if _VERBOSE.value:
            logging.info(
                "%s converted shape=%s with dtype=%s",
                path,
                weights.shape,
                target_dtype,
            )

    for (path, param), value in tree.flatten_with_path(ckpt):
        if param == "audio_input_embedding_extra":
            update_tree("model.embed_audio.embedding.weight", value, config.audio_config.dtype)
        elif path.endswith("audio_embedding_norm"):
            update_tree("model.embed_audio.hard_embedding_norm.weight", value, config.audio_config.dtype)
        elif path.endswith("audio_input_projection"):
            update_tree("model.embed_audio.embedding_projection.weight", value.transpose(), config.audio_config.dtype)
        elif path.endswith("audio_soft_embedding_norm"):
            update_tree("model.embed_audio.soft_embedding_norm.weight", value, config.audio_config.dtype)
        elif param == "mm_input_embedding_extra":
            update_tree("model.embed_vision.embedding.weight", value, config.vision_config.dtype)
        elif path.endswith("mm_hard_embedding_norm"):
            update_tree("model.embed_vision.hard_embedding_norm.weight", value, config.vision_config.dtype)
        elif path.endswith("mm_input_projection"):
            update_tree(
                "model.embed_vision.embedding_projection.weight", value.transpose(), config.vision_config.dtype
            )
        elif path.endswith("mm_soft_embedding_norm"):
            update_tree("model.embed_vision.soft_embedding_norm.weight", value, config.vision_config.dtype)
        elif path.startswith(_TRANSFORMER_PARAMETER):
            for path, weights in convert_transformer_weights(config.text_config, path, param, value):
                update_tree(f"model.language_model.{path}", weights, config.text_config.dtype)
        elif _MOBILE_NET_PREFIX in path:
            mobilenet_prefix_idx = path.index(_MOBILE_NET_PREFIX)
            path = path[mobilenet_prefix_idx:]
            for path, weights in convert_vision_weights(config.vision_config, path, param, value):
                update_tree(f"model.vision_tower.timm_model.{path}", weights, config.vision_config.dtype)
        elif path.startswith(_AUDIO_ENCODER_PARAMETER):
            for path, weights in convert_audio_encoder_weights(config.audio_config, path, param, value):
                update_tree(f"model.audio_tower.{path}", weights, config.audio_config.dtype)

    hf_tree["lm_head.weight"] = hf_tree["model.language_model.embed_tokens.weight"]

    return hf_tree