def _parse_content_to_tables(self, content_data: list[dict[str, Any]]) -> list:
        """Convert parsing results to tables format"""
        tables = []

        for item in content_data:
            if item.get("type") == "table":
                table_data = item.get("table_data", {})
                if isinstance(table_data, dict):
                    rows = table_data.get("rows", [])
                    if rows:
                        # Convert to table format
                        table_html = "<table>\n"
                        for i, row in enumerate(rows):
                            table_html += "  <tr>\n"
                            for cell in row:
                                tag = "th" if i == 0 else "td"
                                table_html += f"    <{tag}>{cell}</{tag}>\n"
                            table_html += "  </tr>\n"
                        table_html += "</table>"
                        tables.append(table_html)

        return tables