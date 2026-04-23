def _ensure_table_format(self, table: Dict) -> Dict[str, Any]:
        """
        Ensure the table has all required fields with proper defaults.

        Args:
            table: Table dictionary to format

        Returns:
            Properly formatted table dictionary
        """
        # Ensure all required fields exist
        formatted_table = {
            'headers': table.get('headers', []),
            'rows': table.get('rows', []),
            'caption': table.get('caption', ''),
            'summary': table.get('summary', ''),
            'metadata': table.get('metadata', {})
        }

        # Ensure metadata has basic fields
        if not formatted_table['metadata']:
            formatted_table['metadata'] = {}

        # Calculate metadata if not provided
        metadata = formatted_table['metadata']
        if 'row_count' not in metadata:
            metadata['row_count'] = len(formatted_table['rows'])
        if 'column_count' not in metadata:
            metadata['column_count'] = len(formatted_table['headers'])
        if 'has_headers' not in metadata:
            metadata['has_headers'] = bool(formatted_table['headers'])

        # Ensure all rows have the same number of columns as headers
        col_count = len(formatted_table['headers'])
        if col_count > 0:
            for i, row in enumerate(formatted_table['rows']):
                if len(row) < col_count:
                    # Pad with empty strings
                    formatted_table['rows'][i] = row + [''] * (col_count - len(row))
                elif len(row) > col_count:
                    # Truncate extra columns
                    formatted_table['rows'][i] = row[:col_count]

        return formatted_table