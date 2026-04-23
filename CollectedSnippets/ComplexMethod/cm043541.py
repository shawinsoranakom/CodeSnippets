def handle_obbject_display(
    obbject: OBBject,
    chart: bool = False,
    export: str = "",
    sheet_name: str = "",
    **kwargs,
):
    """Handle the display of an OBBject."""
    df: pd.DataFrame = pd.DataFrame()
    fig: OpenBBFigure | None = None
    if chart:
        try:
            if obbject.chart:
                obbject.show(**kwargs)
            else:
                obbject.charting.to_chart(**kwargs)  # type: ignore
            if export:
                fig = obbject.chart.fig  # type: ignore
                df = obbject.to_dataframe()
        except Exception as e:
            session.console.print(f"Failed to display chart: {e}")
    elif session.settings.USE_INTERACTIVE_DF:
        obbject.charting.table()  # type: ignore
    else:
        df = obbject.to_dataframe()
        print_rich_table(
            df=df,
            show_index=True,
            title=obbject.extra.get("command", ""),
            export=bool(export),
        )
    if export and not df.empty:
        if sheet_name and isinstance(sheet_name, list):
            sheet_name = sheet_name[0]

        func_name = (
            obbject.extra.get("command", "")
            .replace("/", "_")
            .replace(" ", "_")
            .replace("--", "_")
        )
        export_data(
            export_type=",".join(export),
            dir_path=os.path.dirname(os.path.abspath(__file__)),
            func_name=func_name,
            df=df,
            sheet_name=sheet_name,
            figure=fig,
        )
    elif export and df.empty:
        session.console.print("[yellow]No data to export.[/yellow]")