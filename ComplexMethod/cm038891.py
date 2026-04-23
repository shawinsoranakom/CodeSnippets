def _highlight_threshold(
    df: pd.DataFrame,
    threshold: float,
    slack_pct: float = 0.0,
) -> pd.io.formats.style.Styler:
    conc_col = _find_concurrency_col(df)
    key_cols = [
        c
        for c in ["Model", "Dataset Name", "Input Len", "Output Len", conc_col]
        if c in df.columns
    ]
    conf_cols = [
        c for c in df.columns if c not in key_cols and not str(c).startswith("Ratio")
    ]
    conf_cols = [c for c in conf_cols if pd.api.types.is_numeric_dtype(df[c])]

    try:
        slack_pct = float(slack_pct or 0.0)
    except Exception:
        slack_pct = 0.0
    slack_limit = threshold * (1.0 + slack_pct / 100.0)

    def _cell(v):
        if pd.isna(v):
            return ""
        if v <= threshold:
            # Strict SLA
            return "background-color:#e6ffe6;font-weight:bold;"
        if v <= slack_limit:
            # Within slack range
            return "background-color:#ffe5cc;font-weight:bold;"
        return ""

    return df.style.map(_cell, subset=conf_cols)