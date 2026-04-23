def update_docs_soup(content: str, html_file: Path | None = None, max_title_length: int = 70) -> str:
    """Convert plaintext links to HTML hyperlinks, truncate long meta titles, and remove code line hrefs."""
    title_match = TITLE_PATTERN.search(content)
    needs_title_trim = bool(
        title_match and len(title_match.group(1)) > max_title_length and "-" in title_match.group(1)
    )
    needs_link_conversion = ("<p" in content or "<li" in content) and bool(LINK_PATTERN.search(content))
    needs_codelineno_cleanup = "__codelineno-" in content
    rel_path = ""
    if html_file:
        try:
            rel_path = html_file.relative_to(SITE).as_posix()
        except Exception:
            rel_path = html_file.as_posix()
    needs_kind_highlight = "reference" in rel_path or "reference" in content

    if not (needs_title_trim or needs_link_conversion or needs_codelineno_cleanup or needs_kind_highlight):
        return content

    try:
        soup = BeautifulSoup(content, "lxml")
    except Exception:
        soup = BeautifulSoup(content, "html.parser")
    modified = False

    # Truncate long meta title if needed
    title_tag = soup.find("title") if needs_title_trim else None
    if title_tag and len(title_tag.text) > max_title_length and "-" in title_tag.text:
        title_tag.string = title_tag.text.rsplit("-", 1)[0].strip()
        modified = True

    # Find the main content area
    main_content = soup.find("main") or soup.find("div", class_="md-content")
    if not main_content:
        return str(soup) if modified else content

    # Convert plaintext links to HTML hyperlinks
    if needs_link_conversion:
        for paragraph in main_content.select("p, li"):
            for text_node in paragraph.find_all(string=True, recursive=False):
                if text_node.parent.name not in {"a", "code"}:
                    new_text = LINK_PATTERN.sub(r'<a href="\1">\1</a>', str(text_node))
                    if "<a href=" in new_text:
                        text_node.replace_with(BeautifulSoup(new_text, "html.parser"))
                        modified = True

    # Remove href attributes from code line numbers in code blocks
    if needs_codelineno_cleanup:
        for a in soup.select('a[href^="#__codelineno-"], a[id^="__codelineno-"]'):
            if a.string:  # If the a tag has text (the line number)
                # Check if parent is a span with class="normal"
                if a.parent and a.parent.name == "span" and "normal" in a.parent.get("class", []):
                    del a.parent["class"]
                a.replace_with(a.string)  # Replace with just the text
            else:  # If it has no text
                a.replace_with(soup.new_tag("span"))  # Replace with an empty span
            modified = True

    def highlight_labels(nodes):
        """Inject doc-kind badges into headings and nav entries."""
        nonlocal modified

        for node in nodes:
            if not node.contents:
                continue
            first = node.contents[0]
            if hasattr(first, "get") and "doc-kind" in (first.get("class") or []):
                continue
            text = first if isinstance(first, str) else getattr(first, "string", "")
            if not text:
                continue
            stripped = str(text).strip()
            if not stripped:
                continue
            kind = stripped.split()[0].rstrip(":")
            if kind not in DOC_KIND_LABELS:
                continue
            span = soup.new_tag("span", attrs={"class": f"doc-kind doc-kind-{kind.lower()}"})
            span.string = kind.lower()
            first.replace_with(span)
            tail = str(text)[len(kind) :]
            tail_stripped = tail.lstrip()
            if tail_stripped.startswith(kind):
                tail = tail_stripped[len(kind) :]
            if not tail and len(node.contents) > 0:
                tail = " "
            if tail:
                span.insert_after(tail)
            modified = True

    if "reference" in rel_path:
        highlight_labels(soup.select("main h1, main h2, main h3, main h4, main h5"))
        highlight_labels(soup.select("nav.md-nav--secondary .md-ellipsis, nav.md-nav__list .md-ellipsis"))

    if "reference" in rel_path:
        for ellipsis in soup.select("nav.md-nav--secondary .md-ellipsis"):
            kind = ellipsis.find(class_=lambda c: c and "doc-kind" in c.split())
            text = str(kind.next_sibling).strip() if kind and kind.next_sibling else ellipsis.get_text(strip=True)
            if "." not in text:
                continue
            ellipsis.clear()
            short = text.rsplit(".", 1)[-1]
            if kind:
                ellipsis.append(kind)
                ellipsis.append(f" {short}")
            else:
                ellipsis.append(short)
            modified = True

    if needs_kind_highlight and not modified and soup.select(".doc-kind"):
        # Ensure style injection when pre-existing badges are present
        modified = True

    if modified:
        head = soup.find("head")
        if head and not soup.select("style[data-doc-kind]"):
            style = soup.new_tag("style", attrs={"data-doc-kind": "true"})
            style.string = (
                ".doc-kind{display:inline-flex;align-items:center;gap:0.25em;padding:0.21em 0.59em;border-radius:999px;"
                "font-weight:700;font-size:0.81em;letter-spacing:0.06em;text-transform:uppercase;"
                "line-height:1;color:var(--doc-kind-color,#f8fafc);"
                "background:var(--doc-kind-bg,rgba(255,255,255,0.12));}"
                f".doc-kind-class{{--doc-kind-color:{DOC_KIND_COLORS['Class']};--doc-kind-bg:rgba(3,157,252,0.22);}}"
                f".doc-kind-function{{--doc-kind-color:{DOC_KIND_COLORS['Function']};--doc-kind-bg:rgba(252,152,3,0.22);}}"
                f".doc-kind-method{{--doc-kind-color:{DOC_KIND_COLORS['Method']};--doc-kind-bg:rgba(239,94,255,0.22);}}"
                f".doc-kind-property{{--doc-kind-color:{DOC_KIND_COLORS['Property']};--doc-kind-bg:rgba(2,232,53,0.22);}}"
            )
            head.append(style)

    return str(soup) if modified else content