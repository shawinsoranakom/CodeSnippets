def _validate_grid_stat_uniqueness(value: list[SourceType]) -> list[SourceType]:
    """Validate that grid statistics are unique across all sources."""
    seen_import: set[str] = set()
    seen_export: set[str] = set()
    seen_rate: set[str] = set()

    for source in value:
        if source.get("type") != "grid":
            continue

        # Cast to GridSourceType since we've filtered for grid type
        grid_source: GridSourceType = source  # type: ignore[assignment]

        # Check import meter uniqueness
        if (stat_from := grid_source.get("stat_energy_from")) is not None:
            if stat_from in seen_import:
                raise vol.Invalid(
                    f"Import meter {stat_from} is used in multiple grid connections"
                )
            seen_import.add(stat_from)

        # Check export meter uniqueness
        if (stat_to := grid_source.get("stat_energy_to")) is not None:
            if stat_to in seen_export:
                raise vol.Invalid(
                    f"Export meter {stat_to} is used in multiple grid connections"
                )
            seen_export.add(stat_to)

        # Check power stat uniqueness
        if (stat_rate := grid_source.get("stat_rate")) is not None:
            if stat_rate in seen_rate:
                raise vol.Invalid(
                    f"Power stat {stat_rate} is used in multiple grid connections"
                )
            seen_rate.add(stat_rate)

    return value