def get_en_config() -> dict[str, Any]:
    return mkdocs.utils.yaml_load(en_config_path.read_text(encoding="utf-8"))