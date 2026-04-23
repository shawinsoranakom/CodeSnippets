def from_records(cls, records: list[dict[str, object]]):
        if not isinstance(records, list):
            raise TypeError(
                f"The parameter sweep should be a list of dictionaries, "
                f"but found type: {type(records)}"
            )

        # Validate that all _benchmark_name values are unique if provided
        names = [r["_benchmark_name"] for r in records if "_benchmark_name" in r]
        if names and len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(
                f"Duplicate _benchmark_name values found: {set(duplicates)}. "
                f"All _benchmark_name values must be unique."
            )

        return cls(ParameterSweepItem.from_record(record) for record in records)