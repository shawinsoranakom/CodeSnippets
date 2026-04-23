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