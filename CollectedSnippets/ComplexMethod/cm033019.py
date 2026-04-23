def _build_table_html(self, table_block_id: str) -> str | None:
        rows: list[str] = []
        cursor = None
        while True:
            data = self._fetch_child_blocks(table_block_id, cursor)
            if data is None:
                break

            for result in data["results"]:
                if result.get("type") != "table_row":
                    continue
                cells_html: list[str] = []
                for cell in result["table_row"].get("cells", []):
                    cell_text = self._extract_rich_text(cell)
                    cell_html = html.escape(cell_text) if cell_text else ""
                    cells_html.append(f"<td>{cell_html}</td>")
                rows.append(f"<tr>{''.join(cells_html)}</tr>")

            if data.get("next_cursor") is None:
                break
            cursor = data["next_cursor"]

        if not rows:
            return None
        return "<table>\n" + "\n".join(rows) + "\n</table>"