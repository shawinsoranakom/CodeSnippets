def parse_pages(pages_spec: str, total_pages: int) -> list[int]:
    """Parse 1-based page ranges into 0-based unique page indices."""
    if not pages_spec or not pages_spec.strip():
        raise ValueError("Page ranges are required. Example: 1-5,8,10-12")

    selected_pages = []
    seen_pages = set()

    def add_page(page_number: int):
        if page_number < 1 or page_number > total_pages:
            raise ValueError(
                f"Page {page_number} is out of range. Valid range: 1-{total_pages}"
            )
        page_index = page_number - 1
        if page_index not in seen_pages:
            seen_pages.add(page_index)
            selected_pages.append(page_index)

    for token in [part.strip() for part in pages_spec.split(",") if part.strip()]:
        if "-" in token:
            start_str, end_str = token.split("-", 1)
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError(f"Invalid page range: {token}")
            start_page, end_page = int(start_str), int(end_str)
            if start_page > end_page:
                raise ValueError(
                    f"Invalid page range: {token} (start cannot be greater than end)"
                )
            for page_number in range(start_page, end_page + 1):
                add_page(page_number)
        else:
            if not token.isdigit():
                raise ValueError(f"Invalid page value: {token}")
            add_page(int(token))

    if not selected_pages:
        raise ValueError("No valid pages selected")

    return selected_pages