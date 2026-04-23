def get_all_paths(lang: str):
    res: list[str] = []
    lang_docs_root = Path("docs") / lang / "docs"
    for path in iter_all_lang_paths(lang_docs_root):
        relpath = path.relative_to(lang_docs_root)
        if not str(relpath).startswith(non_translated_sections):
            res.append(str(relpath))
    return res