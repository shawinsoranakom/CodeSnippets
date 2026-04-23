def _resolve_base_model(model_name: str) -> str:
    """If *model_name* points to a LoRA adapter, return its base model.

    Checks for ``adapter_config.json`` locally first.  Only calls the heavier
    ``get_base_model_from_lora`` for paths that are actual local directories
    (avoids noisy warnings for plain HF model IDs).

    Returns the original *model_name* unchanged if it is not a LoRA adapter.
    """
    # --- Fast local check ---------------------------------------------------
    local_path = Path(model_name)
    adapter_cfg_path = local_path / "adapter_config.json"
    if adapter_cfg_path.is_file():
        try:
            with open(adapter_cfg_path) as f:
                cfg = json.load(f)
            base = cfg.get("base_model_name_or_path")
            if base:
                logger.info(
                    "Resolved LoRA adapter '%s' → base model '%s'",
                    model_name,
                    base,
                )
                return base
        except Exception as exc:
            logger.debug("Could not read %s: %s", adapter_cfg_path, exc)

    # --- config.json fallback (works for both LoRA and full fine-tune) ------
    config_json_path = local_path / "config.json"
    if config_json_path.is_file():
        try:
            with open(config_json_path) as f:
                cfg = json.load(f)
            # Unsloth writes "model_name"; HF writes "_name_or_path"
            base = cfg.get("model_name") or cfg.get("_name_or_path")
            if base and base != str(local_path):
                logger.info(
                    "Resolved checkpoint '%s' → base model '%s' (via config.json)",
                    model_name,
                    base,
                )
                return base
        except Exception as exc:
            logger.debug("Could not read %s: %s", config_json_path, exc)

    # --- Only try the heavier fallback for local directories ----------------
    if local_path.is_dir():
        try:
            from utils.models import get_base_model_from_lora

            base = get_base_model_from_lora(model_name)
            if base:
                logger.info(
                    "Resolved LoRA adapter '%s' → base model '%s' "
                    "(via get_base_model_from_lora)",
                    model_name,
                    base,
                )
                return base
        except Exception as exc:
            logger.debug(
                "get_base_model_from_lora failed for '%s': %s",
                model_name,
                exc,
            )

    return model_name