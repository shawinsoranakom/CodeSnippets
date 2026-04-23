def _plot_fig(
    fig_dir: Path,
    fig_group_data: tuple[tuple[tuple[str, str], ...], list[dict[str, object]]],
    row_by: list[str],
    col_by: list[str],
    curve_by: list[str],
    *,
    var_x: str,
    var_y: str,
    filter_by: PlotFilters,
    bin_by: PlotBinners,
    scale_x: str | None,
    scale_y: str | None,
    dry_run: bool,
    fig_name: str,
    error_bars: bool,
    fig_height: float,
    fig_dpi: int,
):
    # Lazy-import matplotlib/pandas/seaborn
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        plt = PlaceholderModule("matplotlib").placeholder_attr("pyplot")
    try:
        import pandas as pd
    except ImportError:
        pd = PlaceholderModule("pandas")
    try:
        import seaborn as sns
    except ImportError:
        sns = PlaceholderModule("seaborn")

    fig_group, fig_data = fig_group_data

    row_groups = full_groupby(
        fig_data,
        key=lambda item: _get_group(item, row_by),
    )
    num_rows = len(row_groups)
    num_cols = max(
        len(full_groupby(row_data, key=lambda item: _get_group(item, col_by)))
        for _, row_data in row_groups
    )

    fig_path = _get_fig_path(fig_dir, fig_group, fig_name)

    print("[BEGIN FIGURE]")
    print(f"Group: {dict(fig_group)}")
    print(f"Grid: {num_rows} rows x {num_cols} cols")
    print(f"Output file: {fig_path}")

    if dry_run:
        print("[END FIGURE]")
        return

    # Convert string "inf", "-inf", and "nan" to their float equivalents
    fig_data = _convert_inf_nan_strings(fig_data)
    df = pd.DataFrame.from_records(fig_data)

    if var_x not in df.columns:
        raise ValueError(
            f"Cannot find {var_x=!r} in parameter sweep results. "
            f"Available variables: {df.columns.tolist()}"
        )
    if var_y not in df.columns:
        raise ValueError(
            f"Cannot find {var_y=!r} in parameter sweep results. "
            f"Available variables: {df.columns.tolist()}"
        )
    for k in row_by:
        if k not in df.columns:
            raise ValueError(
                f"Cannot find row_by={k!r} in parameter sweep results. "
                f"Available variables: {df.columns.tolist()}"
            )
    for k in col_by:
        if k not in df.columns:
            raise ValueError(
                f"Cannot find col_by={k!r} in parameter sweep results. "
                f"Available variables: {df.columns.tolist()}"
            )
    for k in curve_by:
        if k not in df.columns:
            raise ValueError(
                f"Cannot find curve_by={k!r} in parameter sweep results. "
                f"Available variables: {df.columns.tolist()}"
            )

    df = filter_by.apply(df)
    df = bin_by.apply(df)

    if len(df) == 0:
        print(f"No data to plot. Filters: {filter_by}")
        print("[END FIGURE]")
        return

    # Sort by curve_by columns alphabetically for consistent legend ordering
    if curve_by:
        df = df.sort_values(by=curve_by)

    df["row_group"] = (
        pd.concat(
            [k + "=" + df[k].astype(str) for k in row_by],
            axis=1,
        ).agg("\n".join, axis=1)
        if row_by
        else "(All)"
    )

    df["col_group"] = (
        pd.concat(
            [k + "=" + df[k].astype(str) for k in col_by],
            axis=1,
        ).agg("\n".join, axis=1)
        if col_by
        else "(All)"
    )

    if len(curve_by) <= 3:
        hue, style, size, *_ = (*curve_by, None, None, None)

        g = sns.relplot(
            df,
            x=var_x,
            y=var_y,
            hue=hue,
            style=style,
            size=size,
            markers=True,
            errorbar="sd" if error_bars else None,
            kind="line",
            row="row_group",
            col="col_group",
            height=fig_height,
        )
    else:
        df["curve_group"] = (
            pd.concat(
                [k + "=" + df[k].astype(str) for k in curve_by],
                axis=1,
            ).agg("\n".join, axis=1)
            if curve_by
            else "(All)"
        )

        g = sns.relplot(
            df,
            x=var_x,
            y=var_y,
            hue="curve_group",
            markers=True,
            errorbar="sd" if error_bars else None,
            kind="line",
            row="row_group",
            col="col_group",
            height=fig_height,
        )

    if row_by and col_by:
        g.set_titles("{row_name}\n{col_name}")
    elif row_by:
        g.set_titles("{row_name}")
    elif col_by:
        g.set_titles("{col_name}")
    else:
        g.set_titles("")

    if scale_x:
        g.set(xscale=scale_x)
    if scale_y:
        g.set(yscale=scale_y)

    g.savefig(fig_path, dpi=fig_dpi)
    plt.close(g.figure)

    print("[END FIGURE]")