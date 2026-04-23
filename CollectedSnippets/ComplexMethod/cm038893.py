def _config_value_columns(df: pd.DataFrame, conc_col: str) -> list[str]:
    key_cols = [
        c
        for c in ["Model", "Dataset Name", "Input Len", "Output Len"]
        if c in df.columns
    ]
    exclude = set(key_cols + [conc_col, "qps", "QPS"])

    cols: list[str] = []
    for c in df.columns:
        if c in exclude:
            continue
        lc = str(c).lower()
        if lc.startswith("ratio"):
            continue
        if lc.endswith("_name") or lc == "test name" or lc == "test_name":
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols