def add_permalinks(update_existing: bool = False) -> None:
    """
    Add or update header permalinks in all pages of En docs.
    """
    for md_file in en_docs_path.rglob("*.md"):
        add_permalinks_page(md_file, update_existing=update_existing)