def generate_en_path(*, lang: str, path: Path) -> Path:
    en_docs_path = Path("docs/en/docs")
    assert not str(path).startswith(str(en_docs_path)), (
        f"Path must not be inside {en_docs_path}"
    )
    lang_docs_path = Path(f"docs/{lang}/docs")
    out_path = Path(str(path).replace(str(lang_docs_path), str(en_docs_path)))
    return out_path