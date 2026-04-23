def process_element(element, depth=0) -> str:
        """Recursively process element to markdown."""
        if isinstance(element, NavigableString):
            # Preserve Comment nodes as HTML comments in markdown output.
            if isinstance(element, Comment):
                return f"<!--{element}-->\n\n"
            text = str(element)
            # Normalize whitespace: convert tabs/newlines to spaces, collapse multiple spaces
            text = text.replace("\xa0", " ")  # Non-breaking space
            text = re.sub(r"[\t\n\r]+", " ", text)
            text = re.sub(r" +", " ", text)  # Collapse multiple spaces
            return text

        if element.name is None:
            return ""

        if element.name in ["script", "style", "noscript"]:
            return ""

        # Skip "Table of Contents" page-header elements.
        # SEC filings repeat these at every page break.  Two patterns:
        #   1) A simple div/p whose *only* text is the TOC link.
        #   2) A container div (often with min-height style) that holds
        #      a TOC link *plus* a running section name (e.g.
        #      "Notes to Consolidated Financial Statements — (continued)").
        # Both are navigation artefacts, not document content.
        if element.name in ["div", "p"]:
            toc_link = element.find(
                "a",
                href=True,
                string=re.compile(r"^\s*Table of Contents\s*$", re.I),
            )
            if toc_link:
                full_text = element.get_text(separator=" ", strip=True)
                if len(full_text) < 200:
                    return ""  # Skip this navigation / page-header element

        # Also skip h1-h6 navigation headings whose sole text is "Table of Contents".
        # Some SEC filings embed these as page-break separators (e.g. <h5>Table of Contents</h5>).
        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            _h_text = element.get_text(separator=" ", strip=True)
            if re.match(r"^\s*Table of Contents\s*$", _h_text, re.I):
                return ""

        # This handles modern HTML where anchors use id= on div/p/td/etc
        element_id = element.get("id")
        anchor_prefix = ""

        if element_id and element.name != "a":  # Don't double-process <a> tags
            anchor_prefix = f'<a id="{element_id}"></a>'

        # Handle XBRL inline elements (ix:continuation, ix:nonNumeric, etc.)
        # These are containers that should preserve the structure of their children
        if element.name.startswith("ix:"):
            parts = []

            for child in element.children:
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text:
                        parts.append(text)
                else:
                    parts.append(process_element(child, depth + 1))
            # Join with empty string to preserve paragraph breaks (\n\n) from children
            return "".join(parts)

        # Images - use helper to preserve sizes
        if element.name == "img":
            img_md = _convert_image_to_html(element, base_url)

            if img_md:
                return f"\n\n{img_md}\n\n"

            return ""

        # Tables
        if element.name == "table":
            if keep_tables:
                # Detect TOC / page-navigation tables and suppress duplicates.
                # Older SEC exhibits (e.g. IBM 2008 Annual Report) embed a
                # sidebar navigation table on every page.  These tables have
                # section names with page numbers — NOT financial data.
                # Key signal: a row whose first cell says "Management
                # Discussion" (or similar TOC heading) combined with most
                # rows ending in a bare page-number integer.
                tbl_rows = element.find_all("tr")
                if len(tbl_rows) >= 5:
                    _has_toc_heading = False
                    _page_num_rows = 0
                    for _tr in tbl_rows:
                        _cells = _tr.find_all(["td", "th"])
                        if not _cells:
                            continue
                        _first = _cells[0].get_text(strip=True).lower()
                        if _first in (
                            "management discussion",
                            "table of contents",
                        ) or _first.startswith("management\n"):
                            _has_toc_heading = True
                        _last = _cells[-1].get_text(strip=True)
                        if _last.isdigit() and 0 < int(_last) < 300:
                            _page_num_rows += 1
                    if _has_toc_heading and _page_num_rows >= len(tbl_rows) * 0.5:
                        if _seen_toc_table[0]:
                            return ""  # Already emitted one — skip
                        _seen_toc_table[0] = True
                return "\n\n" + convert_table(element, base_url) + "\n\n"
            return ""

        # Headers
        if is_header_element(element):
            anchor_tag = element.find("a", attrs={"name": True})
            anchor_html = anchor_prefix  # Use element's id if present

            if anchor_tag:
                anchor_name = anchor_tag.get("name")
                if anchor_name:
                    anchor_html = f'<a id="{anchor_name}"></a>\n\n'
            elif anchor_prefix:
                anchor_html = anchor_prefix + "\n\n"

            text = get_text_content(element).strip()
            text = re.sub(r"\s+", " ", text)

            if text:
                level = get_header_level(element)
                return f"\n\n{anchor_html}{'#' * level} {text}\n\n"

            return anchor_html if anchor_html else ""

        # Lists
        if element.name == "ul":
            items = []

            for li in element.find_all("li", recursive=False):
                # Check for id on li element
                li_id = li.get("id")
                li_anchor = f'<a id="{li_id}"></a>' if li_id else ""
                item_text = process_element(li, depth + 1).strip()

                if item_text:
                    items.append(f"- {li_anchor}{item_text}")

            result = "\n" + "\n".join(items) + "\n" if items else ""

            return f"{anchor_prefix}{result}" if anchor_prefix else result

        if element.name == "ol":
            items = []

            for i, li in enumerate(element.find_all("li", recursive=False), 1):
                # Check for id on li element
                li_id = li.get("id")
                li_anchor = f'<a id="{li_id}"></a>' if li_id else ""
                item_text = process_element(li, depth + 1).strip()

                if item_text:
                    items.append(f"{i}. {li_anchor}{item_text}")

            result = "\n" + "\n".join(items) + "\n" if items else ""

            return f"{anchor_prefix}{result}" if anchor_prefix else result

        # Paragraphs and divs
        if element.name in ["p", "div"]:
            # Chart divs produced by _build_chart_summary() should be
            # preserved as raw HTML blocks in the markdown output.
            if element.get("class") and "chart" in element.get("class", []):
                return f"\n\n{str(element)}\n\n"

            # Check if this is an inline element (display:inline in style)
            # Be careful not to match "display:inline-block" which is block-level
            style = element.get("style", "")
            is_inline = bool(
                re.search(
                    r"display:\s*inline(?:\s*;|\s*$|(?![a-z-]))", style, re.IGNORECASE
                )
            )
            has_bold = re.search(
                r"font-weight:\s*(bold|bolder|[6-9]00)", style, re.IGNORECASE
            )
            has_italic = re.search(r"font-style:\s*italic", style, re.IGNORECASE)

            # Check if this is a CSS table-row with bullet (display: table-row)
            # These are used as pseudo-lists in SEC filings
            is_table_row = "display: table-row" in style or "display:table-row" in style

            if is_table_row:
                # Look for bullet in first table-cell, text in second
                cells = element.find_all(
                    "div", style=re.compile(r"display:\s*table-cell", re.IGNORECASE)
                )
                if len(cells) >= 2:
                    first_cell_text = cells[0].get_text(strip=True)

                    if first_cell_text in BULLET_CHARS:
                        # This is a bullet item - extract text from remaining cells
                        text = " ".join(
                            c.get_text(separator=" ", strip=True) for c in cells[1:]
                        )
                        text = re.sub(r"\s+", " ", text).strip()
                        if text:
                            return f"\n- {text}"

            # These are section headers where an anchor tag splits bold text
            children_list = list(element.children)
            children_text = []
            skip_until = -1

            for ci, child in enumerate(children_list):
                if ci <= skip_until:
                    continue
                # Check for anchor with bold content followed by sibling bold
                if (
                    isinstance(child, Tag)
                    and child.name == "a"
                    and (child.get("name") or child.get("id"))
                ):
                    inner_b = child.find(["b", "strong"])

                    if inner_b:
                        anchor_text = child.get_text()

                        if anchor_text.strip():
                            # Look for following <b>/<strong> siblings
                            combined = anchor_text
                            last_consumed = ci
                            found_bold_sib = False

                            for j in range(ci + 1, len(children_list)):
                                sib = children_list[j]

                                if (
                                    isinstance(sib, NavigableString)
                                    and sib.strip() == ""
                                ):
                                    last_consumed = j
                                    continue

                                if isinstance(sib, Tag) and sib.name in [
                                    "b",
                                    "strong",
                                ]:
                                    combined += sib.get_text()
                                    last_consumed = j
                                    found_bold_sib = True
                                else:
                                    break

                            if found_bold_sib:
                                anchor_id = child.get("name") or child.get("id")
                                anchor_html = f'<a id="{anchor_id}"></a>\n\n'
                                combined = re.sub(r"\s+", " ", combined).strip()
                                children_text.append(
                                    f"\n\n{anchor_html}### {combined}\n\n"
                                )
                                skip_until = last_consumed
                                continue

                children_text.append(process_element(child, depth + 1))

            text = "".join(children_text).strip()

            if text:
                if is_inline:
                    # Apply bold/italic formatting for CSS-styled inline elements
                    if has_bold and has_italic:
                        text = f"***{text}***"
                    elif has_bold:
                        text = f"**{text}**"
                    elif has_italic:
                        text = f"*{text}*"
                    return f"{anchor_prefix}{text}" if anchor_prefix else text

                # Convert to proper heading + paragraph
                subheading_match = re.match(
                    r"^(\*{2,3})([^*]+)\1\s*\.\s*(.+)$", text, re.DOTALL
                )

                if subheading_match:
                    title = subheading_match.group(2).strip()
                    body = subheading_match.group(3).strip()

                    return f"\n\n{anchor_prefix}#### {title}\n\n{body}\n\n"

                return f"\n\n{anchor_prefix}{text}\n\n"

            return anchor_prefix if anchor_prefix else ""

        # Line breaks
        if element.name == "br":
            return "\n"

        # Horizontal rules
        if element.name == "hr":
            return "\n\n---\n\n"

        # Anchor tags - handle both links and anchor targets
        if element.name == "a":
            name = element.get("name")
            elem_id = element.get("id")  # Modern HTML uses id instead of name
            href = element.get("href")
            text = get_text_content(element).strip()

            # Anchor target (for TOC links to jump to) - support both name and id
            if name or elem_id:
                anchor_id = name or elem_id  # Prefer name, fall back to id
                anchor = f'<a id="{anchor_id}"></a>'

                if text:
                    return f"{anchor}\n{text}"

                return anchor

            # Regular link
            if href and text:
                if (
                    not href.startswith("#")
                    and base_url
                    and not href.startswith(("http://", "https://"))
                ):
                    href = urljoin(base_url, href)

                return f"[{text}]({href})"

            return text or ""

        # Bold - process children to preserve anchors inside
        if element.name in ["b", "strong"]:
            if element.find("img") and not element.get_text(strip=True):
                parts = []

                for child in element.children:
                    parts.append(process_element(child, depth + 1))

                return "".join(parts)

            parts = []

            for child in element.children:
                parts.append(process_element(child, depth + 1))

            inner = "".join(parts).strip()
            inner = re.sub(r"\s+", " ", inner)

            if inner:
                if '<a id="' in inner:
                    match = re.search(r'(<a id="[^"]+"></a>)(.*)', inner)
                    if match:
                        anchor = match.group(1)
                        text = match.group(2).strip()
                        if text:
                            return f"{anchor}**{text}** "

                        return anchor
                # If inner is only asterisks (footnote markers like *, **),
                # escape them to prevent collision with Markdown formatting
                if re.match(r"^\*+$", inner):
                    return inner.replace("*", "\\*")

                return f"**{inner}** "

            return ""

        # Italic - process children to preserve anchors
        if element.name in ["i", "em"]:
            parts = []

            for child in element.children:
                parts.append(process_element(child, depth + 1))

            inner = "".join(parts).strip()

            if inner:
                if '<a id="' in inner:
                    match = re.search(r'(<a id="[^"]+"></a>)(.*)', inner)
                    if match:
                        anchor = match.group(1)
                        text = match.group(2).strip()

                        if text:
                            return f"{anchor}*{text}*"

                        return anchor
                # If inner is only asterisks (footnote markers like *, **),
                # escape them to prevent collision with Markdown formatting
                if re.match(r"^\*+$", inner):
                    return inner.replace("*", "\\*")

                return f"*{inner}*"

            return ""

        # Underline - just process children
        if element.name == "u":
            parts = []

            for child in element.children:
                parts.append(process_element(child, depth + 1))

            return "".join(parts).strip()

        # Superscript - ensure space separation from adjacent text
        # SEC footnotes use <sup>1</sup>Text which concatenates as "1Text" without this
        if element.name == "sup":
            text = element.get_text().strip()
            if text:
                return f"{text} "
            return ""

        # Blockquote
        if element.name == "blockquote":
            parts = []

            for child in element.children:
                parts.append(process_element(child, depth + 1))

            text = "".join(parts).strip()

            if text:
                lines = text.split("\n")
                quoted = "\n".join(f"> {line}" for line in lines)

                return f"\n\n{quoted}\n\n"

            return ""

        # Pre/code
        if element.name == "pre":
            text = element.get_text()

            return f"\n\n```\n{text}\n```\n\n"

        if element.name == "code":
            text = element.get_text()

            if "\n" not in text:
                return f"`{text}`"

            return f"\n```\n{text}\n```\n"

        # Default: process children (including spans, sections, etc.)
        result_list: list = []

        for child in element.children:
            result_list.append(process_element(child, depth + 1))

        inner = "".join(result_list)
        # Prepend anchor if element had an id attribute
        if anchor_prefix and inner.strip():
            return f"{anchor_prefix}{inner}"

        return inner