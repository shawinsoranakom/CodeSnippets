def add_permalinks_pages(pages: list[Path], update_existing: bool = False) -> None:
    """
    Add or update header permalinks in specific pages of En docs.
    """
    for md_file in pages:
        add_permalinks_page(md_file, update_existing=update_existing)