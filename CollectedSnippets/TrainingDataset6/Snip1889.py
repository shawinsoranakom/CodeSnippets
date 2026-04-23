def get_lang_paths() -> list[Path]:
    return sorted(docs_path.iterdir())