def process_table(self, node):
        blocks = []
        header_row = node.find("thead").find("tr") if node.find("thead") else None
        body_rows = node.find("tbody").find_all("tr") if node.find("tbody") else []

        if header_row or body_rows:
            table_width = max(
                len(header_row.find_all(["th", "td"])) if header_row else 0,
                *(len(row.find_all(["th", "td"])) for row in body_rows),
            )

            table_block = self.create_block("table", "", table_width=table_width, has_column_header=bool(header_row))
            blocks.append(table_block)

            if header_row:
                header_cells = [cell.get_text(strip=True) for cell in header_row.find_all(["th", "td"])]
                header_row_block = self.create_block("table_row", header_cells)
                blocks.append(header_row_block)

            for row in body_rows:
                cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
                row_block = self.create_block("table_row", cells)
                blocks.append(row_block)

        return blocks