def _validate_table_structure(self, table: Dict) -> bool:
        """
        Validate that the table has the required structure.

        Args:
            table: Table dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not isinstance(table, dict):
            return False

        # Must have at least headers and rows
        if 'headers' not in table or 'rows' not in table:
            return False

        # Headers should be a list (but might be nested)
        headers = table.get('headers')
        if not isinstance(headers, list):
            return False

        # Flatten headers if nested
        while isinstance(headers, list) and len(headers) == 1 and isinstance(headers[0], list):
            table['headers'] = headers[0]
            headers = table['headers']

        # Rows should be a list
        rows = table.get('rows')
        if not isinstance(rows, list):
            return False

        # Flatten rows if deeply nested
        cleaned_rows = []
        for row in rows:
            # Handle multiple levels of nesting
            while isinstance(row, list) and len(row) == 1 and isinstance(row[0], list):
                row = row[0]
            cleaned_rows.append(row)
        table['rows'] = cleaned_rows

        # Each row should be a list
        for row in table.get('rows', []):
            if not isinstance(row, list):
                return False

        return True