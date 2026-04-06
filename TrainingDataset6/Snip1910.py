def add_permalinks_page(path: Path, update_existing: bool = False):
    """
    Add or update header permalinks in specific page of En docs.
    """

    if not path.is_relative_to(en_docs_path / "docs"):
        raise RuntimeError(f"Path must be inside {en_docs_path}")
    rel_path = path.relative_to(en_docs_path / "docs")

    # Skip excluded sections
    if str(rel_path).startswith(non_translated_sections):
        return

    visible_text_extractor = VisibleTextExtractor()
    updated_lines = []
    in_code_block3 = False
    in_code_block4 = False
    permalinks = set()

    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        # Handle codeblocks start and end
        if not (in_code_block3 or in_code_block4):
            if code_block4_pattern.match(line):
                in_code_block4 = True
            elif code_block3_pattern.match(line):
                in_code_block3 = True
        else:
            if in_code_block4 and code_block4_pattern.match(line):
                in_code_block4 = False
            elif in_code_block3 and code_block3_pattern.match(line):
                in_code_block3 = False

        # Process Headers only outside codeblocks
        if not (in_code_block3 or in_code_block4):
            match = header_pattern.match(line)
            if match:
                hashes, title, _permalink = match.groups()
                if (not _permalink) or update_existing:
                    slug = slugify(
                        visible_text_extractor.extract_visible_text(
                            strip_markdown_links(title)
                        )
                    )
                    if slug in permalinks:
                        # If the slug is already used, append a number to make it unique
                        count = 1
                        original_slug = slug
                        while slug in permalinks:
                            slug = f"{original_slug}_{count}"
                            count += 1
                    permalinks.add(slug)

                    line = f"{hashes} {title} {{ #{slug} }}\n"

        updated_lines.append(line)

    with path.open("w", encoding="utf-8") as f:
        f.writelines(updated_lines)