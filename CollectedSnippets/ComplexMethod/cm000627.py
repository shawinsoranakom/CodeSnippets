def _insert_table(
        self,
        service,
        document_id: str,
        rows: int,
        columns: int,
        index: int,
        content: list[list[str]],
        format_as_markdown: bool,
    ) -> dict:
        # If index is 0, insert at end of document
        if index == 0:
            index = _get_document_end_index(service, document_id)

        # Insert the empty table structure
        requests = [
            {
                "insertTable": {
                    "rows": rows,
                    "columns": columns,
                    "location": {"index": index},
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

        # If no content provided, we're done
        if not content:
            return {"success": True, "rows": rows, "columns": columns}

        # Fetch the document to find cell indexes
        doc = service.documents().get(documentId=document_id).execute()
        body_content = doc.get("body", {}).get("content", [])

        # Find all tables and pick the one we just inserted
        # (the one with highest startIndex that's >= our insert point, or the last one if inserted at end)
        tables_found = []
        for element in body_content:
            if "table" in element:
                tables_found.append(element)

        if not tables_found:
            return {
                "success": True,
                "rows": rows,
                "columns": columns,
                "warning": "Table created but could not find it to populate",
            }

        # If we inserted at end (index was high), take the last table
        # Otherwise, take the first table at or after our insert index
        table_element = None
        # Heuristic: rows * columns * 2 estimates the minimum index space a table
        # occupies (each cell has at least a start index and structural overhead).
        # This helps determine if our insert point was near the document end.
        estimated_table_size = rows * columns * 2
        if (
            index
            >= _get_document_end_index(service, document_id) - estimated_table_size
        ):
            # Likely inserted at end - use last table
            table_element = tables_found[-1]
        else:
            for tbl in tables_found:
                if tbl.get("startIndex", 0) >= index:
                    table_element = tbl
                    break
            if not table_element:
                table_element = tables_found[-1]

        # Extract cell start indexes from the table structure
        # Structure: table -> tableRows -> tableCells -> content[0] -> startIndex
        cell_positions: list[tuple[int, int, int]] = []  # (row, col, start_index)
        table_data = table_element.get("table", {})
        table_rows_list = table_data.get("tableRows", [])

        for row_idx, table_row in enumerate(table_rows_list):
            cells = table_row.get("tableCells", [])
            for col_idx, cell in enumerate(cells):
                cell_content = cell.get("content", [])
                if cell_content:
                    # Get the start index of the first element in the cell
                    first_element = cell_content[0]
                    cell_start = first_element.get("startIndex")
                    if cell_start is not None:
                        cell_positions.append((row_idx, col_idx, cell_start))

        if not cell_positions:
            return {
                "success": True,
                "rows": rows,
                "columns": columns,
                "warning": f"Table created but could not extract cell positions. Table has {len(table_rows_list)} rows.",
            }

        # Sort by index descending so we can insert in reverse order
        # (inserting later content first preserves earlier indexes)
        cell_positions.sort(key=lambda x: x[2], reverse=True)

        cells_populated = 0

        if format_as_markdown:
            # Markdown formatting: process each cell individually since
            # gravitas-md2gdocs requests may have complex interdependencies
            for row_idx, col_idx, cell_start in cell_positions:
                if row_idx < len(content) and col_idx < len(content[row_idx]):
                    cell_text = content[row_idx][col_idx]
                    if not cell_text:
                        continue
                    md_requests = to_requests(cell_text, start_index=cell_start)
                    if md_requests:
                        service.documents().batchUpdate(
                            documentId=document_id, body={"requests": md_requests}
                        ).execute()
                        cells_populated += 1
        else:
            # Plain text: batch all insertions into a single API call
            # Cells are sorted by index descending, so earlier requests
            # don't affect indices of later ones
            all_text_requests = []
            for row_idx, col_idx, cell_start in cell_positions:
                if row_idx < len(content) and col_idx < len(content[row_idx]):
                    cell_text = content[row_idx][col_idx]
                    if not cell_text:
                        continue
                    all_text_requests.append(
                        {
                            "insertText": {
                                "location": {"index": cell_start},
                                "text": cell_text,
                            }
                        }
                    )
                    cells_populated += 1

            if all_text_requests:
                service.documents().batchUpdate(
                    documentId=document_id, body={"requests": all_text_requests}
                ).execute()

        return {
            "success": True,
            "rows": rows,
            "columns": columns,
            "cells_populated": cells_populated,
            "cells_found": len(cell_positions),
        }