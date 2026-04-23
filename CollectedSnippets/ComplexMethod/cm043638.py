def get_ice_bofa_series_id(
    type_: Literal["yield", "yield_to_worst", "total_return", "spread"],
    category: Literal["all", "duration", "eur", "usd"],
    area: Literal["asia", "emea", "eu", "ex_g10", "latin_america", "us"],
    grade: Literal[
        "a",
        "aa",
        "aaa",
        "b",
        "bb",
        "bbb",
        "ccc",
        "crossover",
        "high_grade",
        "high_yield",
        "non_financial",
        "non_sovereign",
        "private_sector",
        "public_sector",
    ],
) -> list[dict]:
    """Get ICE BofA series id."""
    current_dir = os.path.dirname(os.path.realpath(__file__))
    file = "ice_bofa_indices.csv"

    series = []

    with open(Path(current_dir, file), encoding="utf-8") as csv_file_handler:
        csv_reader = csv.DictReader(csv_file_handler)
        for rows in csv_reader:
            row = {key.lstrip("\ufeff"): value for key, value in rows.items()}
            series.append(row)

    filtered_series = []

    units = "index" if type_ == "total_return" else "percent"

    for s in series:
        # pylint: disable=too-many-boolean-expressions
        if (
            s["Type"] == type_
            and s["Units"] == units
            and s["Frequency"] == "daily"
            and s["Asset Class"] == "bonds"
            and s["Category"] == category
            and s["Area"] == area
            and s["Grade"] == grade
        ):
            filtered_series.append(s)

    return filtered_series