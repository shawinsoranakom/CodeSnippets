def _print_snapshot_tabular(
    snapshot: dict[torch.device, dict[str, int]], units: str
) -> None:
    if len(snapshot) == 0:
        print("No memory tracked.")
        return
    try:
        from tabulate import tabulate
    except ImportError as err:
        raise ImportError(
            "Please install tabulate to use the tabulate option."
        ) from err
    divisor = _get_mem_divisor(units)
    table_data = []
    key_list = list(next(iter(snapshot.values())).keys())
    headers = ["Device"] + [
        f"{key.value}" if isinstance(key, _RefType) else f"{key}" for key in key_list
    ]

    for dev, dev_snap in snapshot.items():
        if _rounding_fn(dev_snap[_TOTAL_KEY], divisor, 2) <= 0:
            continue
        row = [str(dev)]
        row.extend(f"{_rounding_fn(v, divisor, 2)} {units}" for v in dev_snap.values())
        table_data.append(row)
    print(tabulate(table_data, headers=headers, tablefmt="rst"))