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