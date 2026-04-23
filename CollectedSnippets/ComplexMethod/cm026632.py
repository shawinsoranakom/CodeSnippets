def _migrate_legacy_grid_to_unified(
    old_grid: dict[str, Any],
) -> list[dict[str, Any]]:
    """Migrate legacy grid format (flow_from/flow_to/power arrays) to unified format.

    Each grid connection can have any combination of import, export, and power -
    all are optional as long as at least one is configured.

    Migration pairs arrays by index position:
    - flow_from[i], flow_to[i], and power[i] combine into grid connection i
    - If arrays have different lengths, missing entries get None for that field
    - The number of grid connections equals max(len(flow_from), len(flow_to), len(power))
    """
    flow_from = old_grid.get("flow_from", [])
    flow_to = old_grid.get("flow_to", [])
    power_list = old_grid.get("power", [])
    cost_adj = old_grid.get("cost_adjustment_day", 0.0)

    new_sources: list[dict[str, Any]] = []
    # Number of grid connections = max length across all three arrays
    # If all arrays are empty, don't create any grid sources
    max_len = max(len(flow_from), len(flow_to), len(power_list))
    if max_len == 0:
        return []

    for i in range(max_len):
        source: dict[str, Any] = {
            "type": "grid",
            "cost_adjustment_day": cost_adj,
        }

        # Import fields from flow_from
        if i < len(flow_from):
            ff = flow_from[i]
            source["stat_energy_from"] = ff.get("stat_energy_from") or None
            source["stat_cost"] = ff.get("stat_cost")
            source["entity_energy_price"] = ff.get("entity_energy_price")
            source["number_energy_price"] = ff.get("number_energy_price")
        else:
            # Export-only entry - set import to None (validation will flag this)
            source["stat_energy_from"] = None
            source["stat_cost"] = None
            source["entity_energy_price"] = None
            source["number_energy_price"] = None

        # Export fields from flow_to
        if i < len(flow_to):
            ft = flow_to[i]
            source["stat_energy_to"] = ft.get("stat_energy_to")
            source["stat_compensation"] = ft.get("stat_compensation")
            source["entity_energy_price_export"] = ft.get("entity_energy_price")
            source["number_energy_price_export"] = ft.get("number_energy_price")
        else:
            source["stat_energy_to"] = None
            source["stat_compensation"] = None
            source["entity_energy_price_export"] = None
            source["number_energy_price_export"] = None

        # Power config at index i goes to grid connection at index i
        if i < len(power_list):
            power = power_list[i]
            if "power_config" in power:
                source["power_config"] = power["power_config"]
            if "stat_rate" in power:
                source["stat_rate"] = power["stat_rate"]

        new_sources.append(source)

    return new_sources