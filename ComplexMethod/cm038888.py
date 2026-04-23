def _find_concurrency_col(df: pd.DataFrame) -> str:
    for c in [
        "# of max concurrency.",
        "# of max concurrency",
        "Max Concurrency",
        "max_concurrency",
        "Concurrency",
    ]:
        if c in df.columns:
            return c

    for c in df.columns:
        if "concurr" in str(c).lower():
            s = df[c]
            if s.dtype.kind in "iu" and s.nunique() > 1 and s.min() >= 1:
                return c

    raise ValueError(
        "Cannot infer concurrency column. "
        "Please rename the column to one of the known names "
        "or add an explicit override (e.g., --concurrency-col)."
    )