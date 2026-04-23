def ols_regression_summary(
    data: list[Data],
    y_column: str,
    x_columns: list[str],
) -> OBBject[Data]:
    """Perform Ordinary Least Squares (OLS) regression.

    This returns the summary object from statsmodels.

    Parameters
    ----------
    data: list[Data]
        Input dataset.
    y_column: str
        Target column.
    x_columns: list[str]
        list of columns to use as exogenous variables.

    Returns
    -------
    OBBject[Data]
        OBBject with the results being summary object.
    """
    # pylint: disable=import-outside-toplevel
    import re  # noqa
    import statsmodels.api as sm  # noqa
    from openbb_core.app.utils import (
        basemodel_to_df,
        get_target_column,
        get_target_columns,
    )

    X = sm.add_constant(get_target_columns(basemodel_to_df(data), x_columns))
    y = get_target_column(basemodel_to_df(data), y_column)

    try:
        X = X.astype(float)
        y = y.astype(float)
    except ValueError as exc:
        raise ValueError("All columns must be numeric") from exc

    results = sm.OLS(y, X).fit()
    results_summary = results.summary()
    results = {}

    for item in results_summary.tables[0].data:
        results[item[0].strip()] = item[1].strip()
        results[item[2].strip()] = str(item[3]).strip()

    table_1 = results_summary.tables[1]
    headers = table_1.data[0]  # Assuming the headers are in the first row
    for i, row in enumerate(table_1.data):
        if i == 0:  # Skipping the header row
            continue
        for j, cell in enumerate(row):
            if j == 0:  # Skipping the row index
                continue
            key = f"{row[0].strip()}_{headers[j].strip()}"  # Combining row index and column header
            results[key] = cell.strip()

    for item in results_summary.tables[2].data:
        results[item[0].strip()] = item[1].strip()
        results[item[2].strip()] = str(item[3]).strip()

    results = {k: v for k, v in results.items() if v}
    clean_results = {}
    for k, v in results.items():
        new_key = re.sub(r"[.,\]\[:-]", "", k).lower().strip().replace(" ", "_")
        clean_results[new_key] = v

    clean_results["raw"] = str(results_summary)

    return OBBject(results=clean_results)