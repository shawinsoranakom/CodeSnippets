def list_llm_translatable() -> list[str]:
    translatable_langs = get_llm_translatable()
    print("LLM translatable languages:", translatable_langs)
    return translatable_langs