def list_removable(language: str) -> list[Path]:
    removable_paths: list[Path] = []
    lang_paths = Path(f"docs/{language}").rglob("*.md")
    for path in lang_paths:
        en_path = generate_en_path(lang=language, path=path)
        if not en_path.exists():
            removable_paths.append(path)
    print(removable_paths)
    return removable_paths