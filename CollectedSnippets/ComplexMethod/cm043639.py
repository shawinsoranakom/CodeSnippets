def get_cp_series_id(maturity, category, grade) -> list[dict]:
    """Get CP series id."""
    current_dir = os.path.dirname(os.path.realpath(__file__))
    file = "commercial_paper.csv"

    series = []

    with open(Path(current_dir, file), encoding="utf-8") as csv_file_handler:
        csv_reader = csv.DictReader(csv_file_handler)
        for rows in csv_reader:
            row = {key.lstrip("\ufeff"): value for key, value in rows.items()}
            series.append(row)

    filtered_series = []

    category = (
        "non_financial"
        if (grade == "a2_p2" and category != "non_financial")
        else category
    )

    for s in series:
        if (
            s["Maturity"] == maturity
            and s["Category"] == category
            and s["Grade"] == grade
        ):
            filtered_series.append(s)

    return filtered_series