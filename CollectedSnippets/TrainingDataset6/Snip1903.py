def ensure_non_translated() -> None:
    """
    Ensure there are no files in the non translatable pages.
    """
    print("Ensuring no non translated pages")
    lang_paths = get_lang_paths()
    error_paths = []
    for lang in lang_paths:
        if lang.name == "en":
            continue
        for non_translatable in non_translated_sections:
            non_translatable_path = lang / "docs" / non_translatable
            if non_translatable_path.exists():
                error_paths.append(non_translatable_path)
    if error_paths:
        print("Non-translated pages found, removing them:")
        for error_path in error_paths:
            print(error_path)
            if error_path.is_file():
                error_path.unlink()
            else:
                shutil.rmtree(error_path)
        raise typer.Exit(1)
    print("No non-translated pages found ✅")