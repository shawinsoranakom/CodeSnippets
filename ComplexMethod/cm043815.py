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