def on_page_markdown(
    markdown: str, *, page: Page, config: MkDocsConfig, files: Files
) -> str:
    # Set metadata["social"]["cards_layout_options"]["title"] to clean title (without
    # permalink)
    title = page.title
    clean_title = title.split("{ #")[0]
    if clean_title:
        page.meta.setdefault("social", {})
        page.meta["social"].setdefault("cards_layout_options", {})
        page.meta["social"]["cards_layout_options"]["title"] = clean_title

    if isinstance(page.file, EnFile):
        for excluded_section in non_translated_sections:
            if page.file.src_path.startswith(excluded_section):
                return markdown
        missing_translation_content = get_missing_translation_content(config.docs_dir)
        header = ""
        body = markdown
        if markdown.startswith("#"):
            header, _, body = markdown.partition("\n\n")
        return f"{header}\n\n{missing_translation_content}\n\n{body}"

    docs_dir_path = Path(config.docs_dir)
    en_docs_dir_path = docs_dir_path.parent.parent / "en/docs"

    if docs_dir_path == en_docs_dir_path:
        return markdown

    # For translated pages add translation banner
    translation_banner_content = get_translation_banner_content(config.docs_dir)
    en_url = "https://fastapi.tiangolo.com/" + page.url.lstrip("/")
    translation_banner_content = translation_banner_content.replace(
        "ENGLISH_VERSION_URL", en_url
    )
    header = ""
    body = markdown
    if markdown.startswith("#"):
        header, _, body = markdown.partition("\n\n")
    return f"{header}\n\n{translation_banner_content}\n\n{body}"