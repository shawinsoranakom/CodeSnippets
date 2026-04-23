def langs_json():
    langs = []
    for lang_path in get_lang_paths():
        if lang_path.is_dir() and lang_path.name in SUPPORTED_LANGS:
            langs.append(lang_path.name)
    print(json.dumps(langs))