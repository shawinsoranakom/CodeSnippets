def extract_tables(self, element: etree.Element, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract all data tables from the HTML element.

        Args:
            element: The HTML element to search for tables
            **kwargs: Additional parameters (can override instance settings)

        Returns:
            List of dictionaries containing extracted table data
        """
        tables_data = []

        # Allow kwargs to override instance settings
        score_threshold = kwargs.get("table_score_threshold", self.table_score_threshold)

        # Find all table elements
        tables = element.xpath(".//table")

        for table in tables:
            # Check if this is a data table (not a layout table)
            if self.is_data_table(table, table_score_threshold=score_threshold):
                try:
                    table_data = self.extract_table_data(table)

                    # Apply minimum size filters if specified
                    if self.min_rows > 0 and len(table_data.get("rows", [])) < self.min_rows:
                        continue
                    if self.min_cols > 0:
                        col_count = len(table_data.get("headers", [])) or (
                            max(len(row) for row in table_data.get("rows", [])) if table_data.get("rows") else 0
                        )
                        if col_count < self.min_cols:
                            continue

                    tables_data.append(table_data)
                except Exception as e:
                    self._log("error", f"Error extracting table data: {str(e)}", "TABLE_EXTRACT")
                    continue

        return tables_data