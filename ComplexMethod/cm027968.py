def calculate_statistics(numbers: List[float]) -> Dict[str, Union[float, str, int]]:
    """
    Calculate basic statistics for a list of numbers.

    Use this function when users ask for statistical analysis
    of a set of numbers (mean, median, mode, etc.).

    Args:
        numbers: List of numbers to analyze

    Returns:
        Dictionary with statistical results
    """
    try:
        if not numbers:
            return {"error": "Cannot calculate statistics for empty list", "status": "error"}

        # Convert to floats and validate
        try:
            nums = [float(x) for x in numbers]
        except (ValueError, TypeError):
            return {"error": "All values must be numbers", "status": "error"}

        # Calculate statistics
        mean = sum(nums) / len(nums)
        sorted_nums = sorted(nums)

        # Median
        n = len(sorted_nums)
        if n % 2 == 0:
            median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
        else:
            median = sorted_nums[n//2]

        # Mode (most frequent value)
        from collections import Counter
        counts = Counter(nums)
        mode_count = max(counts.values())
        modes = [k for k, v in counts.items() if v == mode_count]

        # Standard deviation
        variance = sum((x - mean) ** 2 for x in nums) / len(nums)
        std_dev = math.sqrt(variance)

        return {
            "count": len(nums),
            "mean": round(mean, 2),
            "median": round(median, 2),
            "mode": modes[0] if len(modes) == 1 else modes,
            "min": min(nums),
            "max": max(nums),
            "range": max(nums) - min(nums),
            "standard_deviation": round(std_dev, 2),
            "sum": sum(nums),
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error calculating statistics: {str(e)}",
            "status": "error"
        }