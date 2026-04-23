def _reflow_absolute_layout(html_content: str) -> str | None:
    """Rewrite position:absolute HTML into flowing HTML.

    Uses a *rule-based* approach: the Certent CDM (and similar PDF-to-HTML
    generators) encode table row separators as thin (≤ 2 px high), full-width
    (≥ 500 px) ``position:absolute`` divs.  These horizontal rules provide
    deterministic table detection — text fragments between consecutive rules
    belong to the same table, and their horizontal positions map to columns.

    Non-table text (paragraphs, headings, chart annotations) is rendered
    outside the rule-delimited zones.  When the page contains a side-by-side
    layout (body text on the left, chart on the right), the fragments are
    split into two columns so chart content doesn't pollute paragraph text.

    Returns the rewritten HTML string, or ``None`` if the document does
    not use an absolute-positioned layout and should be processed normally.
    """
    # Quick heuristic: is this an abs-positioned document?
    # Must have MANY absolute-positioned elements, very few <table> tags,
    # AND the characteristic Certent CDM id="aNN" text-fragment pattern.
    _sample = html_content[:50_000]
    _abs_count = len(re.findall(r"position:\s*absolute", _sample, re.I))
    _table_count = len(re.findall(r"<table\b", html_content[:200_000], re.I))
    if _abs_count < 30 or _table_count > 2:
        return None

    _abs_total = len(re.findall(r"position:\s*absolute", html_content, re.I))
    _div_total = len(re.findall(r"<div\b", html_content, re.I))
    if _div_total == 0 or _abs_total / _div_total < 0.4:
        return None

    # Require the Certent CDM text-fragment pattern: divs with
    # id="aNN" (numeric IDs) that carry the actual text content.
    # This is the hallmark of PDF-to-HTML absolute-positioned layouts.
    # Without this, normal filings with many absolute-positioned logos
    # or headers would be incorrectly rewritten.
    _text_frag_count = len(re.findall(r'<div[^>]+id="a\d+"', _sample, re.I))
    if _text_frag_count < 15:
        return None

    # ---- Parse page boundaries ----
    _page_re = re.compile(r'id="Page(\d+)"')
    page_boundaries = list(_page_re.finditer(html_content))
    if not page_boundaries:
        return None

    page_map: dict[int, int] = {int(m.group(1)): m.start() for m in page_boundaries}
    total_pages = max(page_map.keys())

    # ---- Regex toolbox ----
    _tag_re = re.compile(r"<[^>]+>")
    _bold_re = re.compile(r"font-weight:\s*bold", re.I)
    _fsize_re = re.compile(r"font-size:\s*([\d.]+)px", re.I)
    _content_re = re.compile(
        r'(.*?)(?=<div\s+id="a\d+"|<div\s+style="[^"]*position:\s*absolute)',
        re.S,
    )
    _content_end_re = re.compile(r"(.*?)</div>", re.S)

    def _decode_entities(text: str) -> str:
        for ent, ch in _REFLOW_ENTITIES.items():
            text = text.replace(ent, ch)
        text = re.sub(
            r"&#(\d+);",
            lambda m: chr(int(m.group(1))) if int(m.group(1)) < 0x10000 else "",
            text,
        )
        return text

    def _strip_tags(raw: str) -> str:
        return _decode_entities(_tag_re.sub("", raw)).strip()

    # ---- Per-page parser ----
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

    # ---- Table-zone detection ----
    def _identify_table_zones(
        hrules: list[float],
    ) -> list[tuple[float, float]]:
        """Group consecutive full-width rules into table zones.

        Rules separated by < 300 px are considered part of the same table.
        Returns a list of ``(zone_top, zone_bottom)`` pairs.
        """
        if len(hrules) < 2:
            return []
        zones: list[tuple[float, float]] = []
        zone_start = hrules[0]
        zone_end = hrules[0]
        for i in range(1, len(hrules)):
            if hrules[i] - hrules[i - 1] < 300:
                zone_end = hrules[i]
            else:
                if zone_end > zone_start:
                    zones.append((zone_start, zone_end))
                zone_start = hrules[i]
                zone_end = hrules[i]
        if zone_end > zone_start:
            zones.append((zone_start, zone_end))
        return zones

    # ---- Dedup consecutive identical rows ----
    def _dedup_rows(
        rows: list[list[str]],
    ) -> list[list[str]]:
        """Remove consecutive duplicate rows (same text ignoring bold)."""
        if not rows:
            return rows
        _bold_tag = re.compile(r"</?b>")
        result = [rows[0]]
        for row in rows[1:]:
            prev_text = [_bold_tag.sub("", c) for c in result[-1]]
            cur_text = [_bold_tag.sub("", c) for c in row]
            if cur_text != prev_text:
                result.append(row)
            else:
                prev_bold = sum(1 for c in result[-1] if "<b>" in c)
                cur_bold = sum(1 for c in row if "<b>" in c)
                if cur_bold > prev_bold:
                    result[-1] = row
        return result

    # ---- Build table from a rule-delimited zone ----
    def _build_table_from_zone(
        frags: list[tuple[float, float, str, bool, float]],
        rules: list[float],
    ) -> str:
        if not frags or len(rules) < 2:
            return ""

        rules = sorted(rules)

        # Build row bands: text between consecutive rules
        row_bands: list[list[tuple[float, float, str, bool, float]]] = []
        for i in range(len(rules) - 1):
            band_top = rules[i]
            band_bot = rules[i + 1]
            band_frags = [f for f in frags if band_top - 2 <= f[0] <= band_bot + 2]
            if band_frags:
                row_bands.append(band_frags)

        if not row_bands:
            return ""

        # Determine column positions (cluster left coordinates ±20 px)
        all_lefts: list[float] = []
        for band in row_bands:
            for _, lf, _, _, fs in band:
                if fs >= 7:
                    all_lefts.append(lf)
        if not all_lefts:
            return ""

        all_lefts.sort()
        cols: list[float] = []
        col_n: list[int] = []
        for lf in all_lefts:
            merged = False
            for ci in range(len(cols)):
                if abs(lf - cols[ci]) <= 20:
                    cols[ci] = (cols[ci] * col_n[ci] + lf) / (col_n[ci] + 1)
                    col_n[ci] += 1
                    merged = True
                    break
            if not merged:
                cols.append(lf)
                col_n.append(1)
        cols.sort()
        ncols = len(cols)

        # Build raw row data
        raw_rows: list[list[str]] = []
        for band in row_bands:
            band.sort()
            lines: list[list[tuple[float, str, bool, float]]] = []
            cur_top = band[0][0]
            cur: list[tuple[float, str, bool, float]] = []
            for top, lf, text, bold, fs in band:
                if abs(top - cur_top) <= 3:
                    cur.append((lf, text, bold, fs))
                else:
                    if cur:
                        lines.append(cur)
                    cur_top = top
                    cur = [(lf, text, bold, fs)]
            if cur:
                lines.append(cur)

            for line in lines:
                # Skip superscript footnote markers
                main = [
                    (lv, t, b, f)
                    for lv, t, b, f in line
                    if not (f < 7 and re.match(r"^\d[\d,]*$", t.strip()))
                ]
                if not main:
                    continue

                cells = [""] * ncols
                bolds = [False] * ncols
                for lf, text, bold, _fs in main:
                    best = 0
                    best_dist = abs(lf - cols[0])
                    for ci in range(1, ncols):
                        d = abs(lf - cols[ci])
                        if d < best_dist:
                            best_dist = d
                            best = ci
                    if cells[best]:
                        cells[best] += " " + text
                    else:
                        cells[best] = text
                    if bold:
                        bolds[best] = True

                formatted: list[str] = []
                for ci in range(ncols):
                    c = _html_escape(cells[ci])
                    if bolds[ci] and c:
                        c = f"<b>{c}</b>"
                    formatted.append(c)
                raw_rows.append(formatted)

        raw_rows = _dedup_rows(raw_rows)
        if not raw_rows:
            return ""

        # ---- Pre-merge currency-symbol cells (per-row) ----
        # Absolute-positioned layouts produce "$" / "€" / "£" as
        # separate fragments in their own column.  For each row,
        # merge a lone currency cell with the nearest numeric cell
        # to its right so that convert_table() receives clean data
        # (e.g. "$4,602" instead of "$" + "" + "4,602" in three
        # separate cells).
        _CURR_PLAIN = {"$", "\u20ac", "\u00a3"}  # $, €, £
        _re_btag = re.compile(r"</?b>")
        _re_numval = re.compile(r"^\(?\s*[\d,]+\.?\d*\s*\)?\s*%?$")

        for row in raw_rows:
            ci = 0
            while ci < len(row):
                plain = _re_btag.sub("", row[ci]).strip()
                if plain not in _CURR_PLAIN or not plain:
                    ci += 1
                    continue
                # Look right: skip empties, merge into first numeric
                merged = False
                for cj in range(ci + 1, len(row)):
                    tgt_plain = _re_btag.sub("", row[cj]).strip()
                    if not tgt_plain:
                        continue  # skip empty cells
                    if _re_numval.match(tgt_plain):
                        sym_bold = "<b>" in row[ci]
                        tgt_bold = "<b>" in row[cj]
                        combo = plain + tgt_plain
                        if sym_bold or tgt_bold:
                            combo = f"<b>{combo}</b>"
                        row[cj] = combo
                        row[ci] = ""
                        merged = True
                    break  # stop on first non-empty (merge or not)
                ci += 1

        # Remove columns that are entirely empty
        non_empty = [
            ci
            for ci in range(ncols)
            if any(row[ci].strip() for row in raw_rows if ci < len(row))
        ]

        parts: list[str] = ["<table>\n"]
        for row in raw_rows:
            parts.append("<tr>")
            for ci in non_empty:
                parts.append(f"<td>{row[ci]}</td>")
            parts.append("</tr>\n")
        parts.append("</table>\n")
        return "".join(parts)

    # ---- Fragment classification ----
    def _classify_fragments(
        frags: list[tuple[float, float, str, bool, float]],
    ) -> tuple[
        list[tuple[float, float, str, bool, float]],
        list[tuple[float, float, str, bool, float]],
        list[tuple[float, float, str, bool, float]],
    ]:
        """Classify free fragments as body text, chart content, or footnotes.

        Uses **per-page body-font detection** so the same logic works on
        pages where body text is set in 10 px *and* pages where it is set
        in 8 px (common in the business-segment detail pages).

        1. Detect the page's body font size — the most frequent font size
           among left-margin (left < 75 px) fragments.
        2. *Body text*: fragment whose font size is within +/-0.5 px of
           the detected body font and sits at the left margin, **or**
           within +/-0.3 px at any position (right-column text / unruled
           tables).  Large headings (font > 18 px) and bold subheadings
           at the left margin are also body text.
        3. *Footnotes*: fragments near the page bottom (top > 950 px).
        4. *Chart content*: everything else — axis ticks, legend labels,
           chart titles whose font deviates from the body font.

        Returns ``(body_frags, chart_frags, footnote_frags)``.
        """
        if not frags:
            return [], [], []

        # ---- Detect per-page body font size ----
        # Use a tight left margin (< 55 px) so chart axis labels that
        # sit at left ≈ 62–82 px don't bias the detection.
        body_margin_sizes = [
            round(fs, 1)
            for top, left, _, _, fs in frags
            if left < 55 and top < 950 and 5.0 < fs < 18.0
        ]
        body_fs = (
            Counter(body_margin_sizes).most_common(1)[0][0]
            if len(body_margin_sizes) >= 3
            else 10.0
        )

        # ---- Classify each fragment ----
        # Short numeric/currency tokens that look like chart axis ticks
        # are excluded from body text even when their font matches.
        _chart_val = re.compile(r"^-?[$]\d[\d,.]*$|^-?\d+[%]$|^\d{4}$")

        body: list[tuple[float, float, str, bool, float]] = []
        chart: list[tuple[float, float, str, bool, float]] = []
        footnotes: list[tuple[float, float, str, bool, float]] = []

        for frag in frags:
            top, left, _text, _bold, font_size = frag
            stripped = _text.strip()
            is_axis = len(stripped) < 10 and bool(_chart_val.match(stripped))

            if top > 950:
                footnotes.append(frag)
            elif font_size > 18:
                # Large section heading (e.g. "Net Income" at 22.7 px)
                body.append(frag)
            elif left < 75 and abs(font_size - body_fs) <= 0.5 and not is_axis:
                # Body-font fragment at the left margin
                body.append(frag)
            elif abs(font_size - body_fs) <= 0.3 and not is_axis:
                # Body-font fragment anywhere (right column, unruled table)
                body.append(frag)
            elif left < 75 and _bold and len(stripped) > 8:
                # Bold subheading at the left margin
                body.append(frag)
            else:
                chart.append(frag)

        return body, chart, footnotes

    # ---- Free-content (paragraph / heading) builder ----
    def _build_free_content(
        frags: list[tuple[float, float, str, bool, float]],
    ) -> str:
        """Build body text as flowing HTML with lists, headings, paragraphs.

        Handles bullet lists (●/•), section headings (detected by gap),
        first-line-indent paragraph breaks, and preserves per-fragment
        bold formatting.
        """
        if not frags:
            return ""

        frags = sorted(frags)

        # ---- Build lines: group fragments by top (± 2 px) ----
        # Each line: (top, min_left, fragments)
        lines: list[tuple[float, float, list[tuple[float, str, bool, float]]]] = []
        cur_top = frags[0][0]
        cur: list[tuple[float, str, bool, float]] = []
        for top, left, text, bold, fs in frags:
            if abs(top - cur_top) <= 2:
                cur.append((left, text, bold, fs))
            else:
                if cur:
                    cur.sort()
                    lines.append((cur_top, cur[0][0], cur))
                cur_top = top
                cur = [(left, text, bold, fs)]
        if cur:
            cur.sort()
            lines.append((cur_top, cur[0][0], cur))

        # ---- Split ALL-CAPS heading prefixes from mixed-case text ----
        # Certent CDM layouts place section headers like
        # "BUSINESS SEGMENT ANALYSIS" and subsection names like
        # "Business Focus" at the same top coordinate, forming a
        # multi-fragment line.  Split the ALL-CAPS bold prefix into
        # its own line so the single-bold H2 check can fire for each.
        _ALL_CAPS_RE = re.compile(r"^[A-Z][A-Z &,\-/\u2019\u00a0']+$")
        split_lines: list[tuple[float, float, list[tuple[float, str, bool, float]]]] = (
            []
        )
        for line_top, line_left, line_frags in lines:
            if len(line_frags) <= 1:
                split_lines.append((line_top, line_left, line_frags))
                continue

            # Find the boundary: consecutive bold ALL-CAPS fragments
            # at the start, followed by non-ALL-CAPS or non-bold text.
            caps_end = 0
            for idx, (_, ftext, fbold, _) in enumerate(line_frags):
                t = ftext.strip()
                if fbold and t and _ALL_CAPS_RE.match(t):
                    caps_end = idx + 1
                else:
                    break

            if caps_end > 0 and caps_end < len(line_frags):  # pylint: disable=R1716
                # Verify the remaining text starts mixed-case
                rest_text = " ".join(
                    t.strip() for _, t, _, _ in line_frags[caps_end:]
                ).strip()
                if rest_text and not _ALL_CAPS_RE.match(rest_text):
                    caps_frags = line_frags[:caps_end]
                    rest_frags = line_frags[caps_end:]
                    split_lines.append((line_top, caps_frags[0][0], caps_frags))
                    split_lines.append((line_top + 0.1, rest_frags[0][0], rest_frags))
                    continue

            split_lines.append((line_top, line_left, line_frags))

        lines = split_lines

        # ---- Helpers ----
        _BULLET = {"\u25cf", "\u2022"}

        def _has_bullet(
            lf: list[tuple[float, str, bool, float]],
        ) -> bool:
            return any(t.strip() in _BULLET for _, t, _, _ in lf)

        def _strip_bullet(
            lf: list[tuple[float, str, bool, float]],
        ) -> list[tuple[float, str, bool, float]]:
            return [
                (left_, t, b, f) for left_, t, b, f in lf if t.strip() not in _BULLET
            ]

        def _rich(
            lf: list[tuple[float, str, bool, float]],
        ) -> str:
            """Combine fragments preserving per-fragment bold."""
            parts: list[str] = []
            for _, text, bold, _ in lf:
                esc = _html_escape(text)
                if bold and esc.strip():
                    parts.append(f"<b>{esc}</b>")
                else:
                    parts.append(esc)
            return " ".join(parts)

        # Detect common body-left margin for indent paragraph detection
        left_vals = [lf[0][0] for _, _, lf in lines if lf]
        if left_vals:
            _left_counts: dict[int, int] = {}
            for _lv in left_vals:
                _k = round(_lv)
                _left_counts[_k] = _left_counts.get(_k, 0) + 1
            body_left = max(_left_counts, key=_left_counts.get)  # type: ignore[arg-type]
        else:
            body_left = 48

        # Regex for detecting sentence verbs — a strong signal that
        # the text is body-paragraph content, not a heading title.
        _SENTENCE_VERB_RE = re.compile(
            r"\b(?:is|are|was|were|has|have|had|"
            r"offers?|provides?|includes?|presents?|enables?|allows?"
            r"|consists?|describes?|involves?|ensures?|continues?"
            r"|represents?|reflects?|operates?|serves?|manages?"
            r"|oversees?|supports?|covers?|conform[s]?"
            r"|should|shall|will|would|could)\b",
            re.IGNORECASE,
        )

        # ---- Main loop ----
        out: list[str] = []
        in_list = False
        i = 0

        while i < len(lines):
            line_top, line_left, line_frags = lines[i]
            prev_top = lines[i - 1][0] if i > 0 else None
            gap = (line_top - prev_top) if prev_top is not None else 999

            # ---- H2: single bold fragment ----
            # In absolute-positioned SEC layouts a standalone bold
            # line is always a heading — no gap threshold needed.
            # However, bold body-text paragraphs can also appear as
            # single fragments per line; exclude those based on
            # length, casing, and verb-based sentence detection.
            if len(line_frags) == 1:
                _, text, bold, fs = line_frags[0]
                t = text.strip()
                if bold and fs >= 9.5 and len(t) > 3:
                    _is_heading = True
                    # Starts lowercase → mid-sentence fragment
                    if (
                        t[0].islower()
                        or len(t) > 120
                        and not t.isupper()
                        or len(t) > 60
                        and not t.isupper()
                        and _SENTENCE_VERB_RE.search(t)
                        or t.endswith(".")
                        and not re.search(
                            r"\b(?:INC|CORP|LTD|LLC|CO|JR|SR|DR|MR|MS"
                            + r"|U\.S)\.\s*$",
                            t,
                            re.IGNORECASE,
                        )
                    ):
                        _is_heading = False

                    if in_list:
                        out.append("</ul>\n")
                        in_list = False
                    if _is_heading:
                        out.append(f"<h2>{_html_escape(t)}</h2>\n")
                    else:
                        out.append(
                            f'<p data-body-text="1"><b>{_html_escape(t)}</b></p>\n'
                        )
                    i += 1
                    continue

            # ---- H2: very large font ----
            max_fs = max(fs for _, _, _, fs in line_frags)
            if max_fs >= 18:
                if in_list:
                    out.append("</ul>\n")
                    in_list = False
                parts = [_html_escape(t) for _, t, _, _ in line_frags]
                out.append(f"<h2>{' '.join(parts)}</h2>\n")
                i += 1
                continue

            # ---- Section heading: large gap + short + followed by bullet ----
            plain = " ".join(t for _, t, _, _ in line_frags).strip()
            next_is_bullet = i + 1 < len(lines) and _has_bullet(lines[i + 1][2])
            if (
                gap > 22
                and line_left <= 55
                and len(plain) < 50
                and not _has_bullet(line_frags)
                and next_is_bullet
            ):
                if in_list:
                    out.append("</ul>\n")
                    in_list = False
                out.append(f"<h3>{_rich(line_frags)}</h3>\n")
                i += 1
                continue

            # ---- Bullet line: absorb continuations ----
            if _has_bullet(line_frags):
                if not in_list:
                    out.append("<ul>\n")
                    in_list = True
                clean = _strip_bullet(line_frags)
                parts_list = [_rich(clean)]
                j = i + 1
                while j < len(lines):
                    ntop, _, nfrags = lines[j]
                    ngap = ntop - lines[j - 1][0]
                    if ngap <= 18 and not _has_bullet(nfrags):
                        nmax = max(fs for _, _, _, fs in nfrags)
                        if nmax >= 18:
                            break
                        if len(nfrags) == 1 and nfrags[0][2] and nfrags[0][3] >= 9.5:
                            break
                        parts_list.append(_rich(nfrags))
                        j += 1
                    else:
                        break
                out.append(f"<li>{' '.join(parts_list)}</li>\n")
                i = j
                continue

            # ---- Close list if we fell out of bullets ----
            if in_list:
                out.append("</ul>\n")
                in_list = False

            # ---- Paragraph: collect lines (gap ≤ 18 px) ----
            para = [_rich(line_frags)]
            j = i + 1
            while j < len(lines):
                ntop, _, nfrags = lines[j]
                ngap = ntop - lines[j - 1][0]
                if ngap <= 18 and not _has_bullet(nfrags):
                    nmax = max(fs for _, _, _, fs in nfrags)
                    if nmax >= 18:
                        break
                    if len(nfrags) == 1 and nfrags[0][2] and nfrags[0][3] >= 9.5:
                        break
                    # First-line indent → new paragraph
                    if nfrags[0][0] > body_left + 5:
                        break
                    para.append(_rich(nfrags))
                    j += 1
                else:
                    break

            out.append(f"<p>{' '.join(para)}</p>\n")
            i = j

        if in_list:
            out.append("</ul>\n")

        return "".join(out)

    # ---- Chart-summary builder ----
    def _build_chart_summary(
        frags: list[tuple[float, float, str, bool, float]],
    ) -> str:
        """Build a chart placeholder rendered as a <div class="chart">.

        Extracts bold titles and parenthesised descriptions.  The
        resulting ``<div>`` is preserved as raw HTML in the final
        markdown output so downstream consumers can identify and
        render chart blocks with their own styling.
        """
        if not frags:
            return ""

        titles: list[str] = []
        descs: list[str] = []
        seen_titles: set[str] = set()
        seen_descs: set[str] = set()

        for _top, _left, text, bold, fs in sorted(frags):
            t = text.strip()
            if not t:
                continue
            if bold and fs > 9 and len(t) > 3 and t not in seen_titles:
                titles.append(t)
                seen_titles.add(t)
            elif t.startswith("(") and len(t) > 10 and t not in seen_descs:
                descs.append(t)
                seen_descs.add(t)

        if not titles:
            return ""

        label = " / ".join(titles)
        # Build as a SINGLE line so post-processing cleanup steps
        # (e.g. _remove_repeated_page_elements) cannot split the div
        # into individual lines and strip them as short repeats.
        inner = f"<span>{_html_escape(label)}</span>"
        if descs:
            inner += f'<span class="chart-desc">{_html_escape("; ".join(descs))}</span>'
        return f'<div class="chart">{inner}</div>\n'

    # ---- Per-page reflow orchestrator ----
    def _reflow_page(page_num: int) -> str:
        hrules, text_frags = _parse_page(page_num)
        zones = _identify_table_zones(hrules)

        # Classify fragments into table zones vs. free
        table_frags: dict[int, list[tuple[float, float, str, bool, float]]] = {
            zi: [] for zi in range(len(zones))
        }
        free_frags: list[tuple[float, float, str, bool, float]] = []

        for frag in text_frags:
            top = frag[0]
            placed = False
            for zi, (zt, zb) in enumerate(zones):
                if zt - 5 <= top <= zb + 15:
                    table_frags[zi].append(frag)
                    placed = True
                    break
            if not placed:
                free_frags.append(frag)

        # Classify free fragments into body text, chart, and footnotes
        body_frags, chart_frags, footnote_frags = _classify_fragments(free_frags)

        # Collect page segments in vertical order
        segments: list[tuple[float, str]] = []

        for zi, (zt, zb) in enumerate(zones):
            if table_frags[zi]:
                rules_in = [r for r in hrules if zt - 1 <= r <= zb + 1]
                t_html = _build_table_from_zone(table_frags[zi], rules_in)
                if t_html:
                    # Split composite tables (TABLE 5 + 6 + 7 in one
                    # zone) into independent <table> elements so each
                    # gets converted separately by convert_table().
                    _t_soup = BeautifulSoup(t_html, "html.parser")
                    _t_tag = _t_soup.find("table")
                    if _t_tag:
                        _parts = _split_composite_table(_t_tag)
                        if len(_parts) > 1:
                            _offset = 0.0
                            for _p in _parts:
                                if isinstance(_p, str):
                                    segments.append((zt + _offset, f"<p>{_p}</p>"))
                                else:
                                    segments.append((zt + _offset, str(_p)))
                                _offset += 0.01
                        else:
                            segments.append((zt, t_html))
                    else:
                        segments.append((zt, t_html))

        # Body text → paragraphs / headings
        if body_frags:
            body_frags.sort()
            groups: list[list[tuple[float, float, str, bool, float]]] = []
            cur_group = [body_frags[0]]
            for i in range(1, len(body_frags)):
                gap = body_frags[i][0] - body_frags[i - 1][0]
                crosses_zone = any(
                    body_frags[i - 1][0] < zt and body_frags[i][0] > zb
                    for zt, zb in zones
                )
                if crosses_zone or gap > 40:
                    groups.append(cur_group)
                    cur_group = [body_frags[i]]
                else:
                    cur_group.append(body_frags[i])
            groups.append(cur_group)

            for g in groups:
                content = _build_free_content(g)
                if content.strip():
                    segments.append((g[0][0], content))

        # Chart content → compact annotation
        if chart_frags:
            chart_html = _build_chart_summary(chart_frags)
            if chart_html.strip():
                avg_top = sum(f[0] for f in chart_frags) / len(chart_frags)
                segments.append((avg_top, chart_html))

        # Footnotes → rendered as body paragraphs at page bottom
        if footnote_frags:
            fn_html = _build_free_content(footnote_frags)
            if fn_html.strip():
                segments.append((footnote_frags[0][0], fn_html))

        segments.sort(key=lambda s: s[0])
        return "".join(s[1] for s in segments)

    # ---- Main loop: process every page ----
    out_parts: list[str] = ["<html><body>\n"]

    for pg in range(1, total_pages + 1):
        page_html = _reflow_page(pg)
        if page_html:
            out_parts.append(page_html)

    out_parts.append("</body></html>")
    return "".join(out_parts)