def try_get_dense_modules(
    model: str | Path,
    revision: str | None = None,
) -> list[dict[str, Any]] | None:
    try:
        modules = get_hf_file_to_dict("modules.json", model, revision)
        if not modules:
            return None

        if isinstance(modules, dict):
            modules = modules.get("modules", [])

        _DENSE_MODULE_TYPES = {
            "sentence_transformers.models.Dense",
            "pylate.models.Dense.Dense",
        }
        dense_modules = [m for m in modules if m.get("type") in _DENSE_MODULE_TYPES]
        if not dense_modules:
            return None

        layer_configs = []
        for module in dense_modules:
            folder = module.get("path", "")

            config_path = f"{folder}/config.json" if folder else "config.json"
            layer_config = get_hf_file_to_dict(config_path, model, revision)
            if not layer_config:
                continue
            layer_config["folder"] = folder
            layer_configs.append(layer_config)
        return layer_configs
    except Exception:
        return None