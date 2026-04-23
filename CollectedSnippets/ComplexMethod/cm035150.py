def _chart_to_html(self, chart) -> str:
        """Extract chart data as an HTML table."""
        try:
            chart_type_val = chart.chart_type.value if chart.chart_type else 0
            chart_type_name = _CHART_TYPE_NAMES.get(chart_type_val, "Chart")
        except Exception:
            chart_type_name = "Chart"

        try:
            title_text = ""
            try:
                title_text = chart.chart_title.text_frame.text.strip()
            except Exception:
                pass

            # Extract axis info from OOXML
            chart_root = chart._element

            cat_ax_title = ""
            for ax_tag in (f"{_C}catAx", f"{_C}dateAx"):
                ax_el = chart_root.find(f".//{ax_tag}")
                if ax_el is not None:
                    t_el = ax_el.find(f"{_C}title")
                    if t_el is not None:
                        texts = t_el.findall(f".//{_A}t")
                        cat_ax_title = "".join(el.text or "" for el in texts).strip()
                    break

            has_date_ax = chart_root.find(f".//{_C}dateAx") is not None

            val_ax_title = ""
            val_ax_el = chart_root.find(f".//{_C}valAx")
            if val_ax_el is not None:
                t_el = val_ax_el.find(f"{_C}title")
                if t_el is not None:
                    texts = t_el.findall(f".//{_A}t")
                    val_ax_title = "".join(el.text or "" for el in texts).strip()

            plot = chart.plots[0]
            categories = list(plot.categories) if plot.categories else []
            series_list = list(plot.series)

            if not series_list:
                return f"[{chart_type_name}]"

            # Convert Excel date serials to YYYY-MM-DD for date axes
            if has_date_ax and categories:
                from datetime import datetime, timedelta

                converted = []
                for c in categories:
                    try:
                        dt = datetime(1899, 12, 30) + timedelta(days=float(c))
                        converted.append(dt.strftime("%Y-%m-%d"))
                    except (ValueError, TypeError):
                        converted.append(str(c) if c is not None else "")
                categories = converted

            # Collect series names and values
            series_names = []
            series_values = []
            for idx, series in enumerate(series_list):
                try:
                    name = (
                        (series.tx.text if series.tx else "")
                        or val_ax_title
                        or f"Series{idx+1}"
                    )
                except Exception:
                    name = val_ax_title or f"Series{idx+1}"
                series_names.append(name)
                try:
                    vals = [
                        str(round(v, 4)) if v is not None else "" for v in series.values
                    ]
                except Exception:
                    vals = []
                series_values.append(vals)

            # Build HTML table
            html_parts = ["<table>"]
            if title_text:
                html_parts.append(f"<caption>{title_text}</caption>")

            has_header = cat_ax_title or any(name for name in series_names)
            if has_header:
                html_parts.append("<thead><tr>")
                html_parts.append(f"<th>{cat_ax_title}</th>")
                for name in series_names:
                    html_parts.append(f"<th>{name}</th>")
                html_parts.append("</tr></thead>")

            html_parts.append("<tbody>")
            if categories:
                for i, cat in enumerate(categories):
                    html_parts.append(f"<tr><td>{cat}</td>")
                    for vals in series_values:
                        v = vals[i] if i < len(vals) else ""
                        html_parts.append(f"<td>{v}</td>")
                    html_parts.append("</tr>")
            else:
                max_len = max((len(v) for v in series_values), default=0)
                for i in range(max_len):
                    html_parts.append(f"<tr><td>Item{i+1}</td>")
                    for vals in series_values:
                        v = vals[i] if i < len(vals) else ""
                        html_parts.append(f"<td>{v}</td>")
                    html_parts.append("</tr>")
            html_parts.append("</tbody></table>")

            return "\n".join(html_parts)
        except Exception:
            return f"[{chart_type_name}]"