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