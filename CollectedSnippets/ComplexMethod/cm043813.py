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