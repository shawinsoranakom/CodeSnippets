def check_translation(
    doc_lines: list[str],
    en_doc_lines: list[str],
    lang_code: str,
    auto_fix: bool,
    path: str,
) -> list[str]:
    # Fix code includes
    en_code_includes = extract_code_includes(en_doc_lines)
    doc_lines_with_placeholders = replace_code_includes_with_placeholders(doc_lines)
    fixed_doc_lines = replace_placeholders_with_code_includes(
        doc_lines_with_placeholders, en_code_includes
    )
    if auto_fix and (fixed_doc_lines != doc_lines):
        print(f"Fixing code includes in: {path}")
        doc_lines = fixed_doc_lines

    # Fix permalinks
    en_permalinks = extract_header_permalinks(en_doc_lines)
    doc_permalinks = extract_header_permalinks(doc_lines)
    fixed_doc_lines = replace_header_permalinks(
        doc_lines, doc_permalinks, en_permalinks
    )
    if auto_fix and (fixed_doc_lines != doc_lines):
        print(f"Fixing header permalinks in: {path}")
        doc_lines = fixed_doc_lines

    # Fix markdown links
    en_markdown_links = extract_markdown_links(en_doc_lines)
    doc_markdown_links = extract_markdown_links(doc_lines)
    fixed_doc_lines = replace_markdown_links(
        doc_lines, doc_markdown_links, en_markdown_links, lang_code
    )
    if auto_fix and (fixed_doc_lines != doc_lines):
        print(f"Fixing markdown links in: {path}")
        doc_lines = fixed_doc_lines

    # Fix HTML links
    en_html_links = extract_html_links(en_doc_lines)
    doc_html_links = extract_html_links(doc_lines)
    fixed_doc_lines = replace_html_links(
        doc_lines, doc_html_links, en_html_links, lang_code
    )
    if auto_fix and (fixed_doc_lines != doc_lines):
        print(f"Fixing HTML links in: {path}")
        doc_lines = fixed_doc_lines

    # Fix multiline code blocks
    en_code_blocks = extract_multiline_code_blocks(en_doc_lines)
    doc_code_blocks = extract_multiline_code_blocks(doc_lines)
    fixed_doc_lines = replace_multiline_code_blocks_in_text(
        doc_lines, doc_code_blocks, en_code_blocks
    )
    if auto_fix and (fixed_doc_lines != doc_lines):
        print(f"Fixing multiline code blocks in: {path}")
        doc_lines = fixed_doc_lines

    return doc_lines