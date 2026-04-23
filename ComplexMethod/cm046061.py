def _flatten_index_items(index_block):
    """Recursively flatten index (TOC) blocks into markdown list items.

    Strips the trailing tab+page-number from span content and, when target
    location fields are present on the leaf text block, wraps the text in
    a markdown hyperlink pointing to the body-block anchor.

    Styling (bold, italic, underline, strikethrough) is applied via the
    configured office style render mode. HYPERLINK spans are rendered as
    plain styled text (without the URL) because TOC entries use
    document-internal bookmark links, not external URLs.

    The tab+page-number is stripped from the raw content BEFORE markdown
    style markers are applied, so that closing markers (e.g. ``**``) are
    never inadvertently removed by the tab-stripping step.
    """
    items = []
    ilevel = index_block.get('ilevel', 0)
    indent = '    ' * ilevel

    for child in index_block.get('blocks', []):
        if child.get('type') == BlockType.INDEX:
            items.extend(_flatten_index_items(child))
        elif child.get('type') == BlockType.TEXT:
            span_items = []   # list of (content, span_type, span_style)
            anchor = child.get('anchor')
            if not isinstance(anchor, str) or not anchor.strip():
                anchor = None
            else:
                anchor = anchor.strip()

            for line in child.get('lines', []):
                for span in line.get('spans', []):
                    content = span.get('content', '')
                    span_style = span.get('style', [])
                    span_type = span.get('type')
                    span_items.append((content, span_type, span_style))

            if not span_items:
                continue

            # ----------------------------------------------------------
            # Step 1: Strip the trailing tab+page-number from the raw
            # (unstyled) content BEFORE applying markdown markers.
            #
            # Find the last non-equation span that contains a tab; strip
            # everything after its last tab ONLY when the trailing token
            # actually looks like a page number.
            # Then replace any remaining internal tabs with spaces so that
            # "1.1\t研究对象" → "1.1 研究对象".
            # ----------------------------------------------------------
            def _looks_like_page_token(token: str) -> bool:
                token = token.strip()
                if not token:
                    return False
                # Page tokens are usually short and contain no CJK characters.
                if len(token) > 12:
                    return False
                if re.search(r'[\u4e00-\u9fff]', token):
                    return False
                # Arabic / Roman / single-letter page styles.
                if re.fullmatch(r'\d+', token):
                    return True
                if re.fullmatch(r'[ivxlcdm]+', token.lower()):
                    return True
                if re.fullmatch(r'[a-zA-Z]', token):
                    return True
                return False

            last_tab_span_idx = -1
            for i, (content, span_type, _) in enumerate(span_items):
                if span_type != ContentType.INLINE_EQUATION and '\t' in content:
                    last_tab_span_idx = i

            should_strip_page_tail = False
            if last_tab_span_idx != -1:
                last_tab_content = span_items[last_tab_span_idx][0]
                tab_tail = last_tab_content.rsplit('\t', 1)[1]
                should_strip_page_tail = _looks_like_page_token(tab_tail)

            # Build stripped span_items
            stripped_span_items = []
            for i, (content, span_type, span_style) in enumerate(span_items):
                if span_type != ContentType.INLINE_EQUATION:
                    if i == last_tab_span_idx and should_strip_page_tail:
                        # Strip from last tab onwards (removes tab + page number)
                        content = content.rsplit('\t', 1)[0]
                    # Replace remaining internal tabs with spaces
                    content = content.replace('\t', ' ')
                stripped_span_items.append((content, span_type, span_style))

            # ----------------------------------------------------------
            # Step 2: Apply markdown styles and build the final text.
            #
            # If all non-equation spans share the same non-empty style
            # (common in TOC entries like all-bold), apply style once to
            # the whole item to avoid fragmented markers such as
            # "**foo****bar**".
            # ----------------------------------------------------------
            non_eq_styles = [
                tuple(span_style)
                for content, span_type, span_style in stripped_span_items
                if content and span_type != ContentType.INLINE_EQUATION
            ]
            uniform_style = None
            if non_eq_styles:
                first_style = non_eq_styles[0]
                if first_style and all(s == first_style for s in non_eq_styles):
                    uniform_style = list(first_style)

            if uniform_style:
                raw_parts = []
                for content, span_type, _span_style in stripped_span_items:
                    if not content:
                        continue
                    if span_type == ContentType.INLINE_EQUATION:
                        raw_parts.append(
                            f'{inline_left_delimiter}{content}{inline_right_delimiter}'
                        )
                    else:
                        # For TOC rendering, hyperlink spans output as plain text.
                        raw_parts.append(_escape_office_markdown_text(content))
                item_text = ''.join(raw_parts).strip()
                if item_text:
                    item_text = _apply_configured_style(item_text, uniform_style)
            else:
                rendered_parts = []
                for content, span_type, span_style in stripped_span_items:
                    if not content:
                        continue
                    if span_type == ContentType.INLINE_EQUATION:
                        rendered_parts.append(
                            _make_rendered_part(
                                span_type,
                                f'{inline_left_delimiter}{content}{inline_right_delimiter}',
                                raw_content=content,
                            )
                        )
                    elif span_type == ContentType.HYPERLINK:
                        _append_hyperlink_part(
                            rendered_parts,
                            content,
                            span_style,
                            plain_text_only=True,
                        )
                    else:
                        _append_text_part(rendered_parts, content, span_style)

                item_text = _join_rendered_parts(rendered_parts).strip()
            if not item_text:
                continue

            if anchor is not None:
                item_text = _render_link(item_text, f"#{anchor}")

            items.append(f"{indent}- {item_text}")

    return items