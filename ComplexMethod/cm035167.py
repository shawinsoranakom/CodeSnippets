def _extract_chart_tables(para, doc) -> list:
    """Extract chart data as HTML tables from drawings in a paragraph."""
    try:
        from datetime import datetime, timedelta

        results = []
        containers = para._element.findall(f".//{_WPD}inline") + para._element.findall(
            f".//{_WPD}anchor"
        )

        for container in containers:
            chart_ref = container.find(f".//{_C}chart")
            if chart_ref is None:
                continue
            r_id = chart_ref.get(f"{_R}id")
            if not r_id:
                continue
            try:
                rel = doc.part.rels[r_id]
                chart_part = rel.target_part
            except (KeyError, AttributeError):
                continue

            try:
                import lxml.etree as etree

                chart_root = etree.fromstring(chart_part.blob)
            except Exception:
                continue

            # Extract chart title
            title_text = ""
            title_el = chart_root.find(f".//{_C}title")
            if title_el is not None:
                a_t_els = title_el.findall(f".//{_A}t")
                title_text = "".join((el.text or "") for el in a_t_els).strip()

            # Extract axis titles
            cat_ax_title = ""
            for ax_tag in (f"{_C}catAx", f"{_C}dateAx"):
                ax_el = chart_root.find(f".//{ax_tag}")
                if ax_el is not None:
                    t_el = ax_el.find(f"{_C}title")
                    if t_el is not None:
                        texts = t_el.findall(f".//{_A}t")
                        cat_ax_title = "".join(el.text or "" for el in texts).strip()
                        break

            val_ax_title = ""
            val_ax_el = chart_root.find(f".//{_C}valAx")
            if val_ax_el is not None:
                t_el = val_ax_el.find(f"{_C}title")
                if t_el is not None:
                    texts = t_el.findall(f".//{_A}t")
                    val_ax_title = "".join(el.text or "" for el in texts).strip()

            # Extract series data
            series_list = chart_root.findall(f".//{_C}ser")
            if not series_list:
                continue

            # Collect categories from first series
            categories = []
            cat_is_date = False
            date_format_code = ""
            first_ser = series_list[0]
            cat_el = first_ser.find(f"{_C}cat")
            if cat_el is not None:
                str_cache = cat_el.find(f".//{_C}strCache")
                num_cache = cat_el.find(f".//{_C}numCache")
                if str_cache is not None:
                    for pt in str_cache.findall(f"{_C}pt"):
                        v = pt.find(f"{_C}v")
                        categories.append(v.text if v is not None else "")
                elif num_cache is not None:
                    fmt_el = num_cache.find(f"{_C}formatCode")
                    if fmt_el is not None:
                        fc = fmt_el.text or ""
                        date_format_code = fc
                        cat_is_date = any(k in fc.lower() for k in ("y", "m", "d"))
                    for pt in num_cache.findall(f"{_C}pt"):
                        v = pt.find(f"{_C}v")
                        if v is not None and v.text:
                            try:
                                serial = float(v.text)
                                if cat_is_date:
                                    dt = datetime(1899, 12, 30) + timedelta(days=serial)
                                    categories.append(dt.strftime("%Y-%m-%d"))
                                else:
                                    categories.append(v.text)
                            except (ValueError, OverflowError):
                                categories.append(v.text or "")
                        else:
                            categories.append("")

            # Collect series names and values
            series_names = []
            series_values = []
            for ser in series_list:
                # Series name: val axis title > <c:tx> > ""
                name = val_ax_title
                if not name:
                    tx_el = ser.find(f"{_C}tx")
                    if tx_el is not None:
                        str_ref = tx_el.find(f".//{_C}strCache")
                        if str_ref is not None:
                            pt = str_ref.find(f"{_C}pt")
                            if pt is not None:
                                v = pt.find(f"{_C}v")
                                name = v.text if v is not None else ""
                        else:
                            v = tx_el.find(f"{_C}v")
                            if v is not None:
                                name = v.text or ""
                series_names.append(name)

                # Values
                vals = []
                val_el = ser.find(f"{_C}val")
                if val_el is not None:
                    num_cache = val_el.find(f".//{_C}numCache")
                    if num_cache is not None:
                        pts = {
                            int(pt.get("idx", 0)): pt
                            for pt in num_cache.findall(f"{_C}pt")
                        }
                        max_idx = max(pts.keys()) if pts else -1
                        for idx in range(max_idx + 1):
                            pt = pts.get(idx)
                            if pt is not None:
                                v = pt.find(f"{_C}v")
                                vals.append(v.text if v is not None else "")
                            else:
                                vals.append("")
                series_values.append(vals)

            if not series_names:
                continue

            # Build HTML table
            n_rows = max(
                len(categories),
                max((len(v) for v in series_values), default=0),
            )
            html_parts = ["<table>"]
            if title_text:
                html_parts.append(f"<caption>{title_text}</caption>")
            # Header row — omit <thead> entirely if no header info
            has_header = cat_ax_title or any(name for name in series_names)
            if has_header:
                html_parts.append("<thead><tr>")
                html_parts.append(f"<th>{cat_ax_title}</th>")
                for name in series_names:
                    html_parts.append(f"<th>{name}</th>")
                html_parts.append("</tr></thead>")
            # Data rows
            html_parts.append("<tbody>")
            for i in range(n_rows):
                cat = categories[i] if i < len(categories) else ""
                html_parts.append(f"<tr><td>{cat}</td>")
                for vals in series_values:
                    val = vals[i] if i < len(vals) else ""
                    html_parts.append(f"<td>{val}</td>")
                html_parts.append("</tr>")
            html_parts.append("</tbody></table>")
            results.append("".join(html_parts))

        return results
    except Exception:
        return []