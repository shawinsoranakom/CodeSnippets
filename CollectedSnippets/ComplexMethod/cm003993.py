def convert(checkpoint_path: str, config: Gemma4Config) -> dict[str, torch.Tensor]:
    """Loads Orbax checkpoint from `input_path` and converts it to HF tree."""
    ckpt = _restore_checkpoint(checkpoint_path)
    hf_tree: dict[str, torch.Tensor] = {}

    text_path_prefix = "model"
    if not _TEXT_ONLY.value:
        text_path_prefix += ".language_model"

    def update_tree(path: str, weights: np.ndarray, target_dtype: torch.dtype) -> None:
        # Convert directly to float32 in a single step to avoid an extra intermediate copy.
        # The old code did np.asarray(weights) then .astype("float32"), keeping two full copies alive.
        weights_f32 = np.asarray(weights, dtype=np.float32)
        del weights  # allow GC of the input (JAX array or numpy view)
        t = torch.from_numpy(weights_f32)  # shares memory with weights_f32
        if t.dtype != target_dtype:
            hf_tree[path] = t.to(target_dtype)
            del t, weights_f32  # free the float32 intermediate
        else:
            hf_tree[path] = t
        if _VERBOSE.value:
            logging.info(
                "%s converted shape=%s with dtype=%s",
                path,
                hf_tree[path].shape,
                target_dtype,
            )

    for path_tuple, value in tree.flatten_with_path(ckpt):
        param = path_tuple[-1]
        if "params" in path_tuple:
            path_tuple = path_tuple[2:]
        path_tuple = path_tuple[:-1]
        path = "/".join(path_tuple) if len(path_tuple) > 1 else path_tuple[0]

        if path.endswith("audio_input_projection") and not _TEXT_ONLY.value:
            update_tree("model.embed_audio.embedding_projection.weight", value.transpose(), config.audio_config.dtype)
        elif path.endswith("mm_input_projection") and not _TEXT_ONLY.value:
            update_tree(
                "model.embed_vision.embedding_projection.weight", value.transpose(), config.vision_config.dtype
            )
        elif path.startswith(_TRANSFORMER_PARAMETER):
            for hf_path, weights in convert_transformer_weights(config.text_config, path, param, value):
                update_tree(f"{text_path_prefix}.{hf_path}", weights, config.text_config.dtype)
        elif path.startswith(_VISION_ENCODER_PARAMETER) and not _TEXT_ONLY.value:
            for hf_path, weights in convert_vision_encoder_weights(config.vision_config, path, param, value):
                update_tree(f"model.vision_tower.{hf_path}", weights, config.vision_config.dtype)
        elif path.startswith(_AUDIO_ENCODER_PARAMETER) and not _TEXT_ONLY.value:
            for hf_path, weights in convert_audio_encoder_weights(config.audio_config, path, param, value):
                update_tree(f"model.audio_tower.{hf_path}", weights, config.audio_config.dtype)

    hf_tree["lm_head.weight"] = hf_tree[f"{text_path_prefix}.embed_tokens.weight"]

    return hf_tree