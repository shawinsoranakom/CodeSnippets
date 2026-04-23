def _parse_page(
        page_num: int,
    ) -> tuple[list[float], list[tuple[float, float, str, bool, float]]]:
        """Extract horizontal rules and text fragments from a page.

        Returns ``(hrules, text_frags)`` where *hrules* is a sorted list
        of ``top`` positions of full-width rules and *text_frags* is a
        list of ``(top, left, text, bold, font_size)`` tuples.
        """
        p_start = page_map[page_num]
        p_end = page_map.get(page_num + 1, len(html_content))
        page_html = html_content[p_start:p_end]

        hrules: list[float] = []
        text_frags: list[tuple[float, float, str, bool, float]] = []

        for m in re.finditer(
            r'<div\s[^>]*?style="([^"]*position:\s*absolute[^"]*)"[^>]*>',
            page_html,
            re.I,
        ):
            style = m.group(1)

            left_m = re.search(r"left:([\d.]+)px", style)
            top_m = re.search(r"top:([\d.]+)px", style)
            if not (left_m and top_m):
                continue
            left = float(left_m.group(1))
            top = float(top_m.group(1))

            width_m = re.search(r"width:([\d.]+)px", style)
            height_m = re.search(r"height:([\d.]+)px", style)
            width = float(width_m.group(1)) if width_m else 0
            height = float(height_m.group(1)) if height_m else 0

            # Horizontal rule: thin + wide-enough + explicit dimensions.
            # Full-width rules (≥ 500 px) delimit major tables.
            # Medium rules (200–499 px) delimit smaller tables such as
            # "Fiscal Year 2026 Targets" boxes or split-page layouts.
            if height_m and width_m and height <= 2 and width >= 200:
                hrules.append(top)
                continue

            # Skip vertical rules (explicit narrow width, e.g. 1px bars)
            if width_m and width <= 2:
                continue
            # Skip coloured rectangles (chart bars) that have no text id
            if width_m and height_m and width > 5 and height > 5:
                div_tag = page_html[m.start() : m.end()]
                if not re.search(r'id="a\d+"', div_tag):
                    continue

            # Text fragment — must have id="aNN"
            div_tag = page_html[m.start() : m.end()]
            id_m = re.search(r'id="(a\d+)"', div_tag)
            if not id_m:
                continue

            rest = page_html[m.end() : m.end() + 2000]
            cm = _content_re.match(rest)
            if not cm:
                cm = _content_end_re.match(rest)
            if not cm:
                continue

            text = _strip_tags(cm.group(1))
            if not text:
                continue

            if _PAGE_FOOTER_RE.search(text) and top > 950:
                continue

            bold = bool(_bold_re.search(style))
            fs_m = _fsize_re.search(style)
            font_size = float(fs_m.group(1)) if fs_m else 10.0

            text_frags.append((top, left, text, bold, font_size))

        hrules = sorted(set(round(r, 1) for r in hrules))
        text_frags.sort()
        return hrules, text_frags