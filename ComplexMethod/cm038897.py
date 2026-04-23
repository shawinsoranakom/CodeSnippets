def write_report_group_first(
    files: list[str], info_cols: list[str], plan: MetricPlan, args
):
    name_column = "Test name"
    y_axis_col = get_y_axis_col(info_cols, args.xaxis)

    print("comparing : " + ", ".join(files))

    metric_cache: dict[str, tuple[pd.DataFrame, list[str]]] = {}
    group_cols_canonical: list[str] | None = None

    for metric_label in plan.data_cols:
        output_df, raw_data_cols = compare_data_columns(
            files,
            name_column,
            metric_label,
            info_cols,
            plan.drop_column,
            debug=args.debug,
        )

        raw_data_cols = list(raw_data_cols)
        raw_data_cols.insert(0, y_axis_col)

        group_cols = get_group_cols(output_df, info_cols)
        if group_cols_canonical is None:
            group_cols_canonical = group_cols
        else:
            group_cols_canonical = [c for c in group_cols_canonical if c in group_cols]

        metric_cache[metric_label] = (
            output_df.sort_values(by=args.xaxis),
            raw_data_cols,
        )

    if not group_cols_canonical:
        raise ValueError("No canonical group columns found across metrics.")

    first_metric = plan.data_cols[0]
    first_df_sorted, _ = metric_cache[first_metric]
    group_keys = build_group_keys(
        first_df_sorted, group_cols_canonical, sort_cols=[args.xaxis]
    )

    metric_groupbys = {
        metric_label: df.groupby(group_cols_canonical, dropna=False)
        for metric_label, (df, _) in metric_cache.items()
    }

    csv_dir = Path(args.csv_out_dir) if args.csv_out_dir else None
    if csv_dir:
        csv_dir.mkdir(parents=True, exist_ok=True)

    excel_path = args.excel_out or "perf_comparison.xlsx"
    disable_excel = os.getenv("VLLM_COMPARE_DISABLE_EXCEL", "0") == "1"

    # Prefer xlsxwriter for speed; fallback to openpyxl if unavailable.
    excel_engine = (
        os.getenv("VLLM_COMPARE_EXCEL_ENGINE", "xlsxwriter").strip() or "xlsxwriter"
    )
    if excel_engine == "xlsxwriter" and util.find_spec("xlsxwriter") is None:
        excel_engine = "openpyxl"

    excel_engine_kwargs = {}
    if excel_engine == "xlsxwriter":
        # Reduce memory pressure & usually faster writes.
        excel_engine_kwargs = {"options": {"constant_memory": True}}

    xw_ctx = (
        nullcontext(None)
        if disable_excel
        else pd.ExcelWriter(
            excel_path, engine=excel_engine, engine_kwargs=excel_engine_kwargs
        )
    )
    with xw_ctx as xw:
        used_sheets: set[str] = set()
        # ---- Environment sheet (first) ----
        env_sheet = _sanitize_sheet_name("Environment")
        env_df = _load_env_df_for_inputs(args, files)
        if xw is not None:
            if env_df is None or env_df.empty:
                pd.DataFrame(
                    [
                        {
                            "Section": "Environment",
                            "Key": "vllm_env.txt",
                            "Value": "NOT FOUND (or empty)",
                        }
                    ]
                ).to_excel(xw, sheet_name=env_sheet, index=False)
            else:
                env_df.to_excel(xw, sheet_name=env_sheet, index=False)
            used_sheets.add(env_sheet)
        with open("perf_comparison.html", "w", encoding="utf-8") as main_fh:
            main_fh.write('<meta charset="utf-8">\n')
            for gkey in group_keys:
                gkey_tuple = normalize_group_key(gkey)
                suffix = build_group_suffix(group_cols_canonical, gkey_tuple)
                sub_path = group_filename(gkey_tuple)
                group_header = (
                    '<div style="font-size: 1.4em; font-weight: 700; '
                    'margin: 18px 0 10px 0;">'
                    f"{_html.escape(suffix)}"
                    "</div>\n"
                )

                main_fh.write(group_header)

                do_excel = xw is not None
                sheet = _group_to_sheet_base(group_cols_canonical, gkey_tuple)
                sheet_base = sheet
                if do_excel:
                    dedup_i = 1
                    while sheet in used_sheets:
                        dedup_i += 1
                        suffix = f"_{dedup_i}"
                        # Ensure uniqueness even when sheet names are truncated.
                        base = str(sheet_base)
                        keep = max(1, 31 - len(suffix))
                        sheet = _sanitize_sheet_name(base[:keep] + suffix)
                    used_sheets.add(sheet)

                excel_blocks: list[tuple[str, pd.DataFrame]] = []

                with open(sub_path, "w", encoding="utf-8") as sub_fh:
                    sub_fh.write('<meta charset="utf-8">\n')
                    sub_fh.write(group_header)
                    tput_group_df = None
                    ttft_group_df = None
                    tpot_group_df = None
                    conc_col = args.xaxis

                    for metric_label in plan.data_cols:
                        gb = metric_groupbys[metric_label]
                        df_sorted, raw_data_cols = metric_cache[metric_label]

                        try:
                            group_df = gb.get_group(gkey)
                        except KeyError:
                            missing = (
                                '<div style="font-size: 1.1em; font-weight: 600; '
                                'margin: 10px 0;">'
                                f"{_html.escape(metric_label)} — missing for this group"
                                "</div>\n"
                            )
                            main_fh.write(missing)
                            sub_fh.write(missing)
                            continue

                        if conc_col not in group_df.columns:
                            conc_col = _find_concurrency_col(group_df)

                        mn = metric_label.lower().strip()
                        if "tok/s" in mn:
                            tput_group_df = group_df
                        elif "ttft" in mn:
                            ttft_group_df = group_df
                        elif mn in ("p99", "median") or "tpot" in mn:
                            tpot_group_df = group_df

                        display_group = group_df.drop(
                            columns=group_cols_canonical, errors="ignore"
                        )

                        html = render_metric_table_html(
                            display_group, metric_label, suffix, args
                        )
                        main_fh.write(html)
                        sub_fh.write(html)

                        maybe_write_plot(
                            main_fh,
                            sub_fh,
                            group_df=group_df,
                            raw_data_cols=raw_data_cols,
                            metric_label=metric_label,
                            y_axis_col=y_axis_col,
                            args=args,
                        )

                        excel_blocks.append(
                            (metric_label, group_df.reset_index(drop=True))
                        )
                        if csv_dir:
                            fn = _safe_filename(
                                f"{sheet}__{metric_label}".replace(" ", "_").replace(
                                    "/", "_"
                                )
                            )
                            group_df.to_csv(csv_dir / f"{fn}.csv", index=False)

                    summary_html = build_valid_max_concurrency_summary_html(
                        tput_group_df=tput_group_df,
                        ttft_group_df=ttft_group_df,
                        tpot_group_df=tpot_group_df,
                        conc_col=conc_col,
                        args=args,
                    )
                    if summary_html:
                        main_fh.write(summary_html)
                        sub_fh.write(summary_html)

                    summary_df = build_valid_max_concurrency_summary_df(
                        tput_group_df=tput_group_df,
                        ttft_group_df=ttft_group_df,
                        tpot_group_df=tpot_group_df,
                        conc_col=conc_col,
                        args=args,
                    )
                    if summary_df is not None:
                        excel_blocks.append(
                            ("Valid Max Concurrency Summary", summary_df)
                        )
                        if csv_dir:
                            fn = _safe_filename(
                                f"{sheet}__Valid_Max_Concurrency_Summary"
                            )
                            summary_df.to_csv(csv_dir / f"{fn}.csv", index=False)

                if do_excel:
                    _write_tables_to_excel_sheet(xw, sheet, excel_blocks)

    if disable_excel:
        print("Skipped Excel generation (VLLM_COMPARE_DISABLE_EXCEL=1).")
    else:
        print(f"Wrote Excel: {excel_path}")
    if csv_dir:
        print(f"Wrote CSVs under: {csv_dir}")