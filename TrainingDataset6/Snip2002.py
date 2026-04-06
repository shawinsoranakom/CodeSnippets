def list_missing(language: str) -> list[Path]:
    missing_paths: list[Path] = []
    en_lang_paths = list(iter_en_paths_to_translate())
    for path in en_lang_paths:
        lang_path = generate_lang_path(lang=language, path=path)
        if not lang_path.exists():
            missing_paths.append(path)
    print(missing_paths)
    return missing_paths