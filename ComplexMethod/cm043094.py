def extract_tables(self, element, **kwargs):
        """Extract only tables that appear to contain financial data."""
        tables_data = []

        for table in element.xpath(".//table"):
            # Check if table contains currency symbols
            table_text = ''.join(table.itertext())
            has_currency = any(symbol in table_text for symbol in self.currency_symbols)

            if not has_currency:
                continue

            # Extract using base logic (could reuse DefaultTableExtraction logic)
            headers = []
            rows = []

            # Extract headers
            for th in table.xpath(".//thead//th | .//tr[1]//th"):
                headers.append(th.text_content().strip())

            # Extract rows
            for tr in table.xpath(".//tbody//tr | .//tr[position()>1]"):
                row = []
                for td in tr.xpath(".//td"):
                    cell_text = td.text_content().strip()
                    # Clean currency values
                    for symbol in self.currency_symbols:
                        cell_text = cell_text.replace(symbol, '')
                    row.append(cell_text)
                if row:
                    rows.append(row)

            if headers or rows:
                tables_data.append({
                    "headers": headers,
                    "rows": rows,
                    "caption": table.xpath(".//caption/text()")[0] if table.xpath(".//caption") else "",
                    "summary": table.get("summary", ""),
                    "metadata": {
                        "type": "financial",
                        "has_currency": True,
                        "row_count": len(rows),
                        "column_count": len(headers) if headers else len(rows[0]) if rows else 0
                    }
                })

        return tables_data