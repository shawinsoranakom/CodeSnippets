def _process_html_file(html_file: Path) -> bool:
    """Process a single HTML file; returns True if modified."""
    try:
        content = html_file.read_text(encoding="utf-8")
    except Exception as e:
        LOGGER.warning(f"Could not read {html_file}: {e}")
        return False

    changed = False
    try:
        rel_path = html_file.relative_to(SITE).as_posix()
    except ValueError:
        rel_path = html_file.name

    # For pages sourced from external repos (compare), drop edit/copy buttons to avoid wrong links
    if rel_path.startswith("compare/"):
        before = content
        content = re.sub(
            r'<a[^>]*class="[^"]*md-content__button[^"]*"[^>]*>.*?</a>',
            "",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if content != before:
            changed = True

    if rel_path == "404.html":
        new_content = re.sub(r"<title>.*?</title>", "<title>Ultralytics Docs - Not Found</title>", content)
        if new_content != content:
            content, changed = new_content, True

    new_content = update_docs_soup(content, html_file=html_file)
    if new_content != content:
        content, changed = new_content, True

    new_content = _rewrite_md_links(content)
    if new_content != content:
        content, changed = new_content, True

    if changed:
        try:
            html_file.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            LOGGER.warning(f"Could not write {html_file}: {e}")
    return False