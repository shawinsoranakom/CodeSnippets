def _print_state_snapshots_tabular(
    snapshots: dict[_State, list[dict[torch.device, dict[str, int]]]], units: str
) -> None:
    try:
        from tabulate import tabulate
    except ImportError as err:
        raise ImportError(
            "Please install tabulate to use the tabulate option."
        ) from err

    table_data = []
    last_state_call = None
    divisor = _get_mem_divisor(units)
    for state, snapshot_list in snapshots.items():
        for i, snapshot in enumerate(snapshot_list):
            state_call = f"{state.value} # {i + 1}"
            for dev, dev_snap in snapshot.items():
                if _rounding_fn(dev_snap[_TOTAL_KEY], divisor, 2) <= 0:
                    continue
                row = {
                    "State & Call": (
                        state_call if state_call != last_state_call else ""
                    ),
                    "Device": str(dev),
                }
                last_state_call = state_call
                for k, v in dev_snap.items():
                    row[f"{k.value}" if isinstance(k, _RefType) else f"{k}"] = (
                        f"{_rounding_fn(v, divisor, 2)} {units}"
                    )
                table_data.append(row)
    print(tabulate(table_data, headers="keys", tablefmt="rst"))