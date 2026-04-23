def compare_data_columns(
    files: list[str],
    name_column: str,
    data_column: str,
    info_cols: list[str],
    drop_column: str,
    debug: bool = False,
):
    """
    Align concatenation by keys derived from info_cols instead of row order.
    - Pick one canonical key list: subset of info_cols present in ALL files.
    - For each file: set index to those keys, aggregate duplicates
      (mean for metric, first for names).
    - Concat along axis=1 (indexes align), then reset_index so callers can
      group by columns.
    - If --debug, add a <file_label>_name column per file.

    Minimal fix to support different max_concurrency lists across files:
      - normalize concurrency column naming to "# of max concurrency."
      - align on UNION of keys (missing points become NaN)
      - BUGFIX: don't drop throughput rows based on P99/Median presence
    """
    print("\ncompare_data_column:", data_column)

    frames = []
    raw_data_cols: list[str] = []

    # Determine key cols after normalizing concurrency
    cols_per_file: list[set] = []
    for f in files:
        try:
            df_tmp = pd.read_json(f, orient="records")
        except Exception as err:
            raise ValueError(f"Failed to read {f}") from err
        df_tmp = _normalize_concurrency_in_df(df_tmp, canonical="# of max concurrency.")
        cols_per_file.append(set(df_tmp.columns))

    key_cols = [c for c in info_cols if all(c in cset for cset in cols_per_file)]
    if not key_cols:
        key_cols = [c for c in info_cols if c in list(cols_per_file[0])]
    if not key_cols:
        raise ValueError(
            "No common key columns found from info_cols across the input files."
        )

    union_index = None
    metas: list[pd.DataFrame] = []
    staged: list[tuple[str, pd.Series, pd.Series | None]] = []

    for file in files:
        df = pd.read_json(file, orient="records")
        df = _normalize_concurrency_in_df(df, canonical="# of max concurrency.")

        # BUGFIX: only drop rows for latency-like metrics; throughput rows may have
        # NaN in P99/Median columns even if the column exists in the JSON.
        metric_lc = str(data_column).lower()
        is_latency_metric = (
            "ttft" in metric_lc
            or "tpot" in metric_lc
            or "p99" in metric_lc
            or "median" in metric_lc
            or metric_lc.strip() in {"p99", "median"}
        )
        if is_latency_metric and drop_column in df.columns:
            df = df.dropna(subset=[drop_column], ignore_index=True)

        for c in (
            "Input Len",
            "Output Len",
            "TP Size",
            "PP Size",
            "# of max concurrency.",
            "qps",
        ):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        for c in key_cols:
            if c not in df.columns:
                df[c] = pd.NA

        df_idx = df.set_index(key_cols, drop=False)

        meta = df_idx[key_cols]
        if not meta.index.is_unique:
            meta = meta.groupby(level=key_cols, dropna=False).first()

        file_label = "/".join(file.split("/")[:-1]) or os.path.basename(file)

        if data_column in df_idx.columns:
            s = df_idx[data_column]
            if not s.index.is_unique:
                s = s.groupby(level=key_cols, dropna=False).mean()
        else:
            # keep NA series to preserve meta keys for union_index
            s = pd.Series(pd.NA, index=meta.index)
        s.name = file_label

        name_s = None
        if debug and name_column in df_idx.columns:
            name_s = df_idx[name_column]
            if not name_s.index.is_unique:
                name_s = name_s.groupby(level=key_cols, dropna=False).first()
            name_s.name = f"{file_label}_name"

        if union_index is None:
            union_index = meta.index
        else:
            union_index = union_index.union(meta.index)
        metas.append(meta)

        staged.append((file_label, s, name_s))

    if union_index is None:
        raise ValueError("No data found after loading inputs.")

    # meta first (union-aligned): build UNION meta across all files
    if metas:
        meta_union = pd.concat(metas, axis=0)
        # Collapse duplicates on the MultiIndex; keep first non-null per column
        meta_union = meta_union.groupby(level=key_cols, dropna=False).first()
        frames.append(meta_union.reindex(union_index))

    # values + ratios (union-aligned)
    metric_series_aligned: list[pd.Series] = []
    for file_label, s, name_s in staged:
        s_aligned = s.reindex(union_index)
        frames.append(s_aligned)
        raw_data_cols.append(file_label)
        metric_series_aligned.append(s_aligned)

        if debug and name_s is not None:
            frames.append(name_s.reindex(union_index))

        if len(metric_series_aligned) >= 2:
            base = metric_series_aligned[0]
            current = metric_series_aligned[-1]
            if "P99" in str(data_column) or "Median" in str(data_column):
                ratio = base / current
            else:
                ratio = current / base
            ratio = ratio.mask(base == 0)
            ratio.name = f"Ratio 1 vs {len(metric_series_aligned)}"
            frames.append(ratio)

    concat_df = pd.concat(frames, axis=1).reset_index(drop=True)

    front = [c for c in info_cols if c in concat_df.columns]
    rest = [c for c in concat_df.columns if c not in front]
    concat_df = concat_df[front + rest]

    print(raw_data_cols)
    return concat_df, raw_data_cols