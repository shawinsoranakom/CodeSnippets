def build_valid_max_concurrency_summary_df(
    tput_group_df: pd.DataFrame | None,
    ttft_group_df: pd.DataFrame | None,
    tpot_group_df: pd.DataFrame | None,
    conc_col: str,
    args,
) -> pd.DataFrame | None:
    if ttft_group_df is None and tpot_group_df is None:
        return None

    ttft_cols = (
        _config_value_columns(ttft_group_df, conc_col)
        if ttft_group_df is not None
        else []
    )
    tpot_cols = (
        _config_value_columns(tpot_group_df, conc_col)
        if tpot_group_df is not None
        else []
    )
    tput_cols = (
        _config_value_columns(tput_group_df, conc_col)
        if tput_group_df is not None
        else []
    )

    if ttft_group_df is not None and tpot_group_df is not None:
        cfg_cols = [c for c in ttft_cols if c in tpot_cols]
        if tput_group_df is not None:
            cfg_cols = [c for c in cfg_cols if c in tput_cols] or cfg_cols
    else:
        cfg_cols = ttft_cols or tpot_cols

    if not cfg_cols:
        cfg_cols = sorted(set(ttft_cols) | set(tpot_cols) | set(tput_cols), key=str)

    ttft_hi = args.ttft_max_ms * (1.0 + args.ttft_slack_pct / 100.0)
    tpot_hi = args.tpot_max_ms * (1.0 + args.tpot_slack_pct / 100.0)
    ttft_range = f"{args.ttft_max_ms:g}–{ttft_hi:g} ms (+{args.ttft_slack_pct:g}%)"
    tpot_range = f"{args.tpot_max_ms:g}–{tpot_hi:g} ms (+{args.tpot_slack_pct:g}%)"

    rows = []
    for cfg in cfg_cols:
        ttft_max = (
            _max_concurrency_ok(
                ttft_group_df, conc_col, cfg, args.ttft_max_ms, args.ttft_slack_pct
            )
            if ttft_group_df is not None
            else pd.NA
        )
        tpot_max = (
            _max_concurrency_ok(
                tpot_group_df, conc_col, cfg, args.tpot_max_ms, args.tpot_slack_pct
            )
            if tpot_group_df is not None
            else pd.NA
        )
        both = (
            pd.NA
            if (pd.isna(ttft_max) or pd.isna(tpot_max))
            else min(ttft_max, tpot_max)
        )

        tput_at_both = (
            _value_at_concurrency(tput_group_df, conc_col, cfg, both)
            if tput_group_df is not None
            else pd.NA
        )
        ttft_at_both = (
            _value_at_concurrency(ttft_group_df, conc_col, cfg, both)
            if ttft_group_df is not None
            else pd.NA
        )
        tpot_at_both = (
            _value_at_concurrency(tpot_group_df, conc_col, cfg, both)
            if tpot_group_df is not None
            else pd.NA
        )

        rows.append(
            {
                "Configuration": cfg,
                f"Max {conc_col} (TTFT ≤ {ttft_range})": ttft_max,
                f"Max {conc_col} (TPOT ≤ {tpot_range})": tpot_max,
                f"Max {conc_col} (Both)": both,
                "Output Tput @ Both (tok/s)": tput_at_both,
                "TTFT @ Both (ms)": ttft_at_both,
                "TPOT @ Both (ms)": tpot_at_both,
            }
        )

    df = pd.DataFrame(rows)
    for c in df.columns:
        if c != "Configuration":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df