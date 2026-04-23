def statistics_calc(
        self,
        numbers: list[float],
        operations: list[str] | None = None,
    ) -> str:
        """Calculate statistics on a list of numbers.

        Args:
            numbers: List of numbers
            operations: Which statistics to compute

        Returns:
            str: JSON with requested statistics
        """
        if not numbers:
            raise CommandExecutionError("Empty list provided")

        all_ops = [
            "mean",
            "median",
            "mode",
            "stdev",
            "variance",
            "min",
            "max",
            "sum",
            "count",
        ]
        ops = operations if operations else all_ops

        result = {}
        errors = []

        for op in ops:
            try:
                if op == "mean":
                    result["mean"] = statistics.mean(numbers)
                elif op == "median":
                    result["median"] = statistics.median(numbers)
                elif op == "mode":
                    try:
                        result["mode"] = statistics.mode(numbers)
                    except statistics.StatisticsError:
                        result["mode"] = None
                        errors.append("No unique mode found")
                elif op == "stdev":
                    if len(numbers) > 1:
                        result["stdev"] = statistics.stdev(numbers)
                    else:
                        result["stdev"] = 0
                elif op == "variance":
                    if len(numbers) > 1:
                        result["variance"] = statistics.variance(numbers)
                    else:
                        result["variance"] = 0
                elif op == "min":
                    result["min"] = min(numbers)
                elif op == "max":
                    result["max"] = max(numbers)
                elif op == "sum":
                    result["sum"] = sum(numbers)
                elif op == "count":
                    result["count"] = len(numbers)
                else:
                    errors.append(f"Unknown operation: {op}")
            except Exception as e:
                errors.append(f"{op}: {e}")

        output: dict[str, Any] = {"statistics": result}
        if errors:
            output["errors"] = errors

        return json.dumps(output, indent=2)