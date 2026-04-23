def list_all_removable() -> list[Path]:
    all_removable_paths: list[Path] = []
    langs = get_langs()
    for lang in langs:
        if lang == "en":
            continue
        removable_paths = list_removable(lang)
        all_removable_paths.extend(removable_paths)
    print(all_removable_paths)
    return all_removable_paths