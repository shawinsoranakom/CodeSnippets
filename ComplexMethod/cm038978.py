def generate_batch_specs_from_ranges(ranges: list[dict]) -> list[str]:
    """
    Generate batch specs from range specifications.

    Args:
        ranges: List of range specifications, each containing:
            - template: Batch spec template (e.g., "q{q_len}kv1k")
            - q_len: Dict with start, stop, step, end_inclusive (optional)
            - Other parameters can also be ranges

    Returns:
        List of generated batch spec strings

    Example:
        ranges = [
            {
                "template": "q{q_len}kv1k",
                "q_len": {
                    "start": 1,
                    "stop": 16,
                    "step": 1,
                    "end_inclusive": true  # Optional, defaults to true
                }
            }
        ]
        Returns: ["q1kv1k", "q2kv1k", ..., "q16kv1k"]
    """
    all_specs = []

    for range_spec in ranges:
        template = range_spec.get("template")
        if not template:
            raise ValueError("Range specification must include 'template'")

        # Extract all range parameters from the spec
        range_params = {}
        for key, value in range_spec.items():
            if key == "template":
                continue
            if isinstance(value, dict) and "start" in value:
                # This is a range specification
                start = value["start"]
                stop = value["stop"]
                step = value.get("step", 1)
                # Check if end should be inclusive (default: True)
                end_inclusive = value.get("end_inclusive", True)

                # Adjust stop based on end_inclusive
                if end_inclusive:
                    range_params[key] = list(range(start, stop + 1, step))
                else:
                    range_params[key] = list(range(start, stop, step))
            else:
                # This is a fixed value
                range_params[key] = [value]

        # Generate all combinations (Cartesian product)
        if range_params:
            import itertools

            param_names = list(range_params.keys())
            param_values = [range_params[name] for name in param_names]

            for values in itertools.product(*param_values):
                params = dict(zip(param_names, values))
                spec = template.format(**params)
                all_specs.append(spec)
        else:
            # No parameters, just use template as-is
            all_specs.append(template)

    return all_specs