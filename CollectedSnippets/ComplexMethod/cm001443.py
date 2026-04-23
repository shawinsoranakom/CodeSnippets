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