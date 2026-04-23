def get_printable_results(experiment_groups: list[ExperimentGroup]) -> list[str]:
    edge_over_aten = defaultdict(list)
    output = []

    for experiment_group in experiment_groups:
        group_config_name = experiment_group.config.name()
        output.append(f"\nExperiment group: {group_config_name}")

        table_data = calculate_table_data(experiment_group.results)
        for name, edge in zip(table_data["name"], table_data[PERF_OVER_ATEN_STR]):
            edge_over_aten[name].append(edge)
        output.append(
            tabulate(table_data, headers="keys", tablefmt="pretty", floatfmt=".3f")
        )

    if "aten" in edge_over_aten:
        output.append("\nAverage edge over aten (max(-edge, 0), higher is better):")
        for name in edge_over_aten:
            if name != "aten":
                values = [
                    max(-v, 0.0)
                    for v in edge_over_aten[name]
                    if v != float("inf") and v != "NA"
                ]
                valid_count = len(values)
                average_edge = sum(values) / valid_count if values else "No valid data"
                output.append(
                    f"{name}: {average_edge} (from {valid_count} valid values)"
                )
        output.append("\n")

    return "\n".join(output)