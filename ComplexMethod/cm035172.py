def _extract_headers_footers(doc) -> tuple:
    """Extract header and footer text from all document sections.

    Returns (header_lines: list[str], footer_lines: list[str]).
    Deduplicates content and filters out page-number-only text.
    """

    def _collect_from_parts(parts, seen: set) -> list:
        results = []
        for part in parts:
            try:
                if part.is_linked_to_previous:
                    continue
                texts = []
                for para in part.paragraphs:
                    try:
                        items = list(_iter_paragraph_items(para))
                        inline = _runs_to_markdown(items)
                        if not inline:
                            inline = para.text.strip()
                        if inline:
                            texts.append(inline)
                    except Exception:
                        pass
                text = " ".join(texts)
                # Filter: skip empty text, pure digits (page numbers),
                # page-number patterns (e.g. "第  页", "第6页", "共 页"), and duplicates
                if (
                    text
                    and not text.strip().isdigit()
                    and not _RE_PAGE_ONLY.match(text.strip())
                    and text not in seen
                ):
                    seen.add(text)
                    results.append(text)
            except Exception:
                pass
        return results

    header_lines = []
    footer_lines = []
    seen_headers: set = set()
    seen_footers: set = set()

    # Check if the document uses different odd/even page headers/footers
    try:
        odd_even = doc.settings.odd_and_even_pages_header_footer
    except Exception:
        odd_even = False

    for section in doc.sections:
        try:
            # Collect headers
            hdrs = [section.header]
            if odd_even:
                try:
                    hdrs.append(section.even_page_header)
                except Exception:
                    pass
            try:
                if section.different_first_page_header_footer:
                    hdrs.append(section.first_page_header)
            except Exception:
                pass
            header_lines.extend(_collect_from_parts(hdrs, seen_headers))

            # Collect footers
            ftrs = [section.footer]
            if odd_even:
                try:
                    ftrs.append(section.even_page_footer)
                except Exception:
                    pass
            try:
                if section.different_first_page_header_footer:
                    ftrs.append(section.first_page_footer)
            except Exception:
                pass
            footer_lines.extend(_collect_from_parts(ftrs, seen_footers))
        except Exception:
            pass

    return header_lines, footer_lines