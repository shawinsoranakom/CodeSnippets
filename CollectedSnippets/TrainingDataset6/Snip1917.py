def get_translation_banner_content(docs_dir: str) -> str:
    docs_dir_path = Path(docs_dir)
    translation_banner_path = docs_dir_path / "translation-banner.md"
    if not translation_banner_path.is_file():
        translation_banner_path = (
            docs_dir_path.parent.parent / "en" / "docs" / "translation-banner.md"
        )
    return translation_banner_path.read_text(encoding="utf-8")