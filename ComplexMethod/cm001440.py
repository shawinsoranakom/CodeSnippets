def filter_csv(
        self,
        csv_string: str,
        column: str,
        operator: Literal["eq", "ne", "gt", "lt", "gte", "lte", "contains"],
        value: str,
    ) -> str:
        """Filter CSV rows based on a column condition.

        Args:
            csv_string: The CSV string to filter
            column: Column name or index
            operator: Comparison operator
            value: Value to compare against

        Returns:
            str: Filtered CSV as JSON
        """
        # Parse CSV
        data = json.loads(self.parse_csv(csv_string))

        if not data:
            return json.dumps([])

        def compare(row_value: Any, op: str, comp_value: str) -> bool:
            # Try numeric comparison
            try:
                row_num = float(row_value)
                comp_num = float(comp_value)
                if op == "eq":
                    return row_num == comp_num
                elif op == "ne":
                    return row_num != comp_num
                elif op == "gt":
                    return row_num > comp_num
                elif op == "lt":
                    return row_num < comp_num
                elif op == "gte":
                    return row_num >= comp_num
                elif op == "lte":
                    return row_num <= comp_num
            except (ValueError, TypeError):
                pass

            # String comparison
            row_str = str(row_value).lower()
            comp_str = comp_value.lower()

            if op == "eq":
                return row_str == comp_str
            elif op == "ne":
                return row_str != comp_str
            elif op == "contains":
                return comp_str in row_str
            elif op in ("gt", "lt", "gte", "lte"):
                # String comparison for non-numeric
                if op == "gt":
                    return row_str > comp_str
                elif op == "lt":
                    return row_str < comp_str
                elif op == "gte":
                    return row_str >= comp_str
                elif op == "lte":
                    return row_str <= comp_str

            return False

        filtered = []
        for row in data:
            if isinstance(row, dict):
                if column in row:
                    if compare(row[column], operator, value):
                        filtered.append(row)
            elif isinstance(row, list):
                try:
                    col_idx = int(column)
                    if col_idx < len(row):
                        if compare(row[col_idx], operator, value):
                            filtered.append(row)
                except ValueError:
                    pass

        return json.dumps(filtered, indent=2)