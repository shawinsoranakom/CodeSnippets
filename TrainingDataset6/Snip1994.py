def get_llm_translatable() -> list[str]:
    translatable_langs = []
    langs = get_langs()
    for lang in langs:
        if lang == "en":
            continue
        lang_prompt_path = Path(f"docs/{lang}/llm-prompt.md")
        if lang_prompt_path.exists():
            translatable_langs.append(lang)
    return translatable_langs