def generate_hover_html(row):
        """Generate HTML content for hover tooltip."""
        html_parts: list = []

        port_name = row.get("port_full_name", "Unknown Port")
        html_parts.append(f"<b>{port_name}</b><br>")

        # Share of Country's Maritime Traffic
        share_import = row.get("share_country_maritime_import")
        share_export = row.get("share_country_maritime_export")

        traffic_lines_content: list = []
        if share_import is not None:
            traffic_lines_content.append(
                f"&nbsp;&nbsp;&nbsp;&nbsp;Imports:&nbsp;&nbsp;&nbsp;&nbsp;{share_import:.2%}<br>"
            )
        if share_export is not None:
            traffic_lines_content.append(
                f"&nbsp;&nbsp;&nbsp;&nbsp;Exports:&nbsp;&nbsp;&nbsp;&nbsp;{share_export:.2%}<br>"
            )

        if traffic_lines_content:
            html_parts.append("<br><b>Share of Country's Maritime Traffic</b>:<br>")
            html_parts.extend(traffic_lines_content)

        # Avg Annual Vessels
        vessel_labels = [
            "Total",
            "Containers",
            "Tankers",
            "Dry Bulk",
            "General Cargo",
            "Ro-Ro",
        ]
        vessel_cols = [
            "vessel_count_total",
            "vessel_count_container",
            "vessel_count_tanker",
            "vessel_count_dry_bulk",
            "vessel_count_general_cargo",
            "vessel_count_roro",
        ]
        spaces_after_colon = {
            "Total": 17,
            "Containers": 7,
            "Tankers": 12,
            "Dry Bulk": 11,
            "General Cargo": 1,
            "Ro-Ro": 14,
        }

        vessel_lines_content: list = []
        for label, col_name in zip(vessel_labels, vessel_cols):
            count = row.get(col_name)
            if count is not None:
                num_spaces = spaces_after_colon.get(label, 1)
                space_str = "&nbsp;" * num_spaces
                vessel_lines_content.append(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;{label}:{space_str}{count:,}<br>"
                )

        if vessel_lines_content:
            html_parts.append("<br><b>Avg Annual Vessels</b>:<br>")
            html_parts.extend(vessel_lines_content)

        industry_lines_content: list = []
        for i in [1, 2, 3]:
            industry = row.get(f"industry_top{i}")
            if industry and isinstance(industry, str) and industry.strip():
                industry_lines_content.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{industry}<br>")

        if industry_lines_content:
            html_parts.append("<br><b>Top Industries</b>:<br>")
            html_parts.extend(industry_lines_content)

        return "".join(html_parts)