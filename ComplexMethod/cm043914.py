def pivot_indicator_mode(
    df: "pd.DataFrame",
    dates: list[Any],
    countries: list[str],
) -> "pd.DataFrame":
    """Pivot table for indicator mode.

    Creates DataFrame with ["title", "country", "unit", "scale"] as index and dates as columns.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing IMF indicator data.
    dates : list[Any]
        List of dates to use as columns.
    countries : list[str]
        List of countries.

    Returns
    -------
    pd.DataFrame
        Pivoted DataFrame with title, country, unit, and scale as index.
    """
    # pylint: disable=import-outside-toplevel
    import pandas as pd

    rows: list[dict[str, Any]] = []
    # Group by title (indicator name), country, AND unit/scale
    for title in df["title"].unique():
        if pd.isna(title):
            continue
        title_df = df[df["title"] == title]
        for country in countries:
            country_df = title_df[title_df["country"] == country]
            if len(country_df) == 0:
                continue

            # Group by unique unit/scale combinations within this title+country
            # First, extract unit/scale for each row with fallback
            country_df = country_df.copy()
            units = []
            scales = []
            for _, data_row in country_df.iterrows():
                row_unit = data_row.get("unit")
                row_scale = data_row.get("scale")
                # Treat "-" as missing
                if row_unit == "-":
                    row_unit = None
                if row_scale == "-":
                    row_scale = None
                if not row_unit or not row_scale:
                    parsed_unit, parsed_scale = extract_unit_scale_from_title(
                        str(data_row.get("title") or "")
                    )
                    if not row_unit and parsed_unit:
                        row_unit = parsed_unit
                    if not row_scale and parsed_scale:
                        row_scale = parsed_scale
                units.append(row_unit if row_unit else None)
                scales.append(row_scale if row_scale else None)

            country_df["_unit"] = units
            country_df["_scale"] = scales

            # Group by unit/scale and create one output row per group
            for (unit_val, scale_val), group_df in country_df.groupby(
                ["_unit", "_scale"], dropna=False
            ):
                row: dict[str, Any] = {
                    "title": title,
                    "country": country,
                }
                if unit_val is not None:
                    row["unit"] = unit_val

                if scale_val is not None:
                    row["scale"] = scale_val

                # Track if row has any non-zero values
                has_nonzero_value = False
                for d in dates:
                    val = group_df[group_df["date"] == d]["value"].values
                    if len(val) > 0 and pd.notna(val[0]):
                        row[str(d)] = val[0]
                        if val[0] != 0:
                            has_nonzero_value = True
                    else:
                        row[str(d)] = None

                # Skip rows where all date values are 0 or None
                if not has_nonzero_value:
                    continue

                rows.append(row)

    result_df = pd.DataFrame(rows)
    if not result_df.empty:
        result_df = result_df.set_index(["title", "country", "unit", "scale"])

    return result_df