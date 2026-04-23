def _filter_params(
    params: ParameterSweep, *, supported: set[str], strict: bool
) -> ParameterSweep:
    filtered = []
    for item in params:
        kept: dict[str, object] = {}
        dropped: list[str] = []
        for key, value in item.items():
            if _is_supported_param(key, supported):
                kept[key] = value
            else:
                dropped.append(key)

        if dropped:
            label = item.get("_benchmark_name") or item.as_text()
            message = (
                "Ignoring unsupported startup params"
                f"{' for ' + str(label) if label else ''}: "
                f"{', '.join(sorted(dropped))}"
            )
            if strict:
                raise ValueError(message)
            print(message)

        filtered.append(ParameterSweepItem.from_record(kept))

    return ParameterSweep(filtered)