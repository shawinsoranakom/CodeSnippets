def iter_en_paths_to_translate() -> Iterable[Path]:
    en_docs_root = Path("docs/en/docs/")
    for path in iter_all_en_paths():
        relpath = path.relative_to(en_docs_root)
        if not str(relpath).startswith(non_translated_sections):
            yield path