def aggregate_csv(
        self,
        csv_string: str,
        column: str,
        operation: Literal["sum", "avg", "min", "max", "count"],
        group_by: str | None = None,
    ) -> str:
        """Aggregate data in a CSV column.

        Args:
            csv_string: The CSV string to aggregate
            column: Column name to aggregate
            operation: Aggregation operation
            group_by: Optional grouping column

        Returns:
            str: Aggregation result as JSON
        """
        data = json.loads(self.parse_csv(csv_string))

        if not data:
            return json.dumps({"result": None, "error": "No data"})

        def aggregate(values: list) -> float | int | None:
            # Filter to numeric values
            numeric = []
            for v in values:
                try:
                    numeric.append(float(v))
                except (ValueError, TypeError):
                    continue

            if not numeric:
                if operation == "count":
                    return len(values)
                return None

            if operation == "sum":
                return sum(numeric)
            elif operation == "avg":
                return sum(numeric) / len(numeric)
            elif operation == "min":
                return min(numeric)
            elif operation == "max":
                return max(numeric)
            elif operation == "count":
                return len(values)
            return None

        if group_by:
            # Group by operation
            groups: dict[str, list] = {}
            for row in data:
                if isinstance(row, dict):
                    key = str(row.get(group_by, ""))
                    value = row.get(column)
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(value)

            result = {key: aggregate(values) for key, values in groups.items()}
            return json.dumps({"grouped_by": group_by, "results": result}, indent=2)
        else:
            # Simple aggregation
            values = []
            for row in data:
                if isinstance(row, dict):
                    values.append(row.get(column))

            return json.dumps(
                {"column": column, "operation": operation, "result": aggregate(values)},
                indent=2,
            )