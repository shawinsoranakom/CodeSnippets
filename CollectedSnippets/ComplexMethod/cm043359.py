def extract_table_data(self, table: etree.Element) -> Dict[str, Any]:
        """
        Extract structured data from a table element.

        Args:
            table: The table element to extract data from

        Returns:
            Dictionary containing:
                - headers: List of column headers
                - rows: List of row data (each row is a list)
                - caption: Table caption if present
                - summary: Table summary attribute if present
                - metadata: Additional metadata about the table
        """
        # Extract caption and summary
        caption = table.xpath(".//caption/text()")
        caption = caption[0].strip() if caption else ""
        summary = table.get("summary", "").strip()

        # Extract headers with colspan handling
        headers = []
        thead_rows = table.xpath(".//thead/tr")
        if thead_rows:
            header_cells = thead_rows[0].xpath(".//th")
            for cell in header_cells:
                text = cell.text_content().strip()
                colspan = int(cell.get("colspan", 1))
                headers.extend([text] * colspan)
        else:
            # Check first row for headers
            first_row = table.xpath(".//tr[1]")
            if first_row:
                for cell in first_row[0].xpath(".//th|.//td"):
                    text = cell.text_content().strip()
                    colspan = int(cell.get("colspan", 1))
                    headers.extend([text] * colspan)

        # Extract rows with colspan handling
        rows = []
        for row in table.xpath(".//tr[not(ancestor::thead)]"):
            row_data = []
            for cell in row.xpath(".//td"):
                text = cell.text_content().strip()
                colspan = int(cell.get("colspan", 1))
                row_data.extend([text] * colspan)
            if row_data:
                rows.append(row_data)

        # Align rows with headers
        max_columns = len(headers) if headers else (
            max(len(row) for row in rows) if rows else 0
        )
        aligned_rows = []
        for row in rows:
            aligned = row[:max_columns] + [''] * (max_columns - len(row))
            aligned_rows.append(aligned)

        # Generate default headers if none found
        if not headers and max_columns > 0:
            headers = [f"Column {i+1}" for i in range(max_columns)]

        # Build metadata
        metadata = {
            "row_count": len(aligned_rows),
            "column_count": max_columns,
            "has_headers": bool(thead_rows) or bool(table.xpath(".//tr[1]/th")),
            "has_caption": bool(caption),
            "has_summary": bool(summary)
        }

        # Add table attributes that might be useful
        if table.get("id"):
            metadata["id"] = table.get("id")
        if table.get("class"):
            metadata["class"] = table.get("class")

        return {
            "headers": headers,
            "rows": aligned_rows,
            "caption": caption,
            "summary": summary,
            "metadata": metadata
        }