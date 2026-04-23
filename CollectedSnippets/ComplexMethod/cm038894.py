def _max_concurrency_ok(
    df: pd.DataFrame,
    conc_col: str,
    cfg_col: str,
    threshold: float,
    slack_pct: float = 0.0,
):
    if df is None or conc_col not in df.columns or cfg_col not in df.columns:
        return pd.NA

    d = df[[conc_col, cfg_col]].copy()
    d[conc_col] = pd.to_numeric(d[conc_col], errors="coerce")
    d[cfg_col] = pd.to_numeric(d[cfg_col], errors="coerce")
    d = d.dropna(subset=[conc_col, cfg_col])

    if d.empty:
        return pd.NA

    # Accept values up to (1 + slack_pct%) above the SLA.
    try:
        slack_pct = float(slack_pct or 0.0)
    except Exception:
        slack_pct = 0.0
    effective_limit = float(threshold) * (1.0 + slack_pct / 100.0)

    ok = d[d[cfg_col] <= effective_limit]
    if ok.empty:
        return pd.NA

    return ok[conc_col].max()