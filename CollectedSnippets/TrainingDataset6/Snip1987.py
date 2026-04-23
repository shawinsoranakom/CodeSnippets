def get_langs() -> dict[str, str]:
    return yaml.safe_load(Path("docs/language_names.yml").read_text(encoding="utf-8"))