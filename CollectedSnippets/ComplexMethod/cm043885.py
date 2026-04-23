async def presentation_table(
    dataflow_group: Annotated[
        str | None,
        Query(
            title="Dataflow Group",
            description="The IMF dataflow group."
            + " See presentation_table_choices() for options.",
        ),
    ] = None,
    table: Annotated[
        str | None,
        Query(
            title="Table",
            description="The IMF presentation table ID."
            + " See presentation_table_choices() for options.",
        ),
    ] = None,
    country: Annotated[
        str | None,
        Query(
            title="Country",
            description="Country code to filter the data."
            + " Enter multiple codes by joining on '+'. See presentation_table_choices() for options."
            + " Typical values are ISO3 country codes.",
        ),
    ] = None,
    frequency: Annotated[
        str | None,
        Query(
            title="Frequency",
            description="The data frequency. See presentation_table_choices() for options."
            + " Typical values are 'A' (annual), 'Q' (quarter), 'M' (month), or 'D' (day).",
        ),
    ] = None,
    dimension_values: Annotated[
        list[str] | str | None,
        Query(
            title="Dimension Values",
            description="Dimension selection for filtering. Format: 'DIM_ID1:VAL1+VAL2.'"
            + " See presentation_table_choices() and list_dataflow_choices() for available dimensions and values.",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            title="Limit",
            description="Maximum number of records to retrieve per series.",
        ),
    ] = 1,
    raw: Annotated[
        bool,
        Query(
            title="Raw Output",
            description="Return presentation table as raw JSON data if True.",
        ),
    ] = False,
) -> Any:
    """Get a formatted presentation table from the IMF database. Returns as HTML or JSON list."""
    # pylint: disable=import-outside-toplevel
    import html as html_module

    from openbb_imf.models.economic_indicators import ImfEconomicIndicatorsFetcher
    from pandas import DataFrame

    if dataflow_group is None or table is None:
        raise OpenBBError(ValueError("Please enter a dataflow group and a table."))

    if country is None or frequency is None:
        raise OpenBBError(ValueError("Please enter a country and frequency."))

    freq_map = {"A": "annual", "Q": "quarter", "M": "month", "D": "day"}
    symbol = PRESENTATION_TABLES.get(table, "")
    params = {
        "symbol": symbol,
        "country": country,
        "limit": limit,
        "frequency": freq_map.get(frequency, frequency),
        "dimension_values": dimension_values,
        "pivot": True,
    }
    results = await ImfEconomicIndicatorsFetcher.fetch_data(params, {})
    results_json = [d.model_dump(mode="json", exclude_none=True) for d in results.result]  # type: ignore

    if raw is True:
        return results_json

    df = DataFrame(results_json).set_index(["title", "country"]).reset_index()
    # Preserve leading whitespace by replacing double spaces with non-breaking spaces
    df["title"] = df["title"].apply(
        lambda x: x.replace("  ", "\u00a0\u00a0") if isinstance(x, str) else x
    )

    columns = df.columns.tolist()
    header_cells = "".join(
        f"<th>{html_module.escape(str(col))}</th>" for col in columns
    )

    def format_number(value):
        """Format large numbers with K, M, B suffixes for readability."""
        if isinstance(value, (int, float)):
            abs_value = abs(value)
            if abs_value >= 1_000_000_000:
                return f"{value / 1_000_000_000:.2f}".rstrip("0").rstrip(".") + "B"
            if abs_value >= 1_000_000:
                return f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".") + "M"
            if abs_value >= 1_000:
                return f"{value / 1_000:.2f}".rstrip("0").rstrip(".") + "K"
            if isinstance(value, float):
                return f"{value:.2f}".rstrip("0").rstrip(".")
            return str(value)
        return str(value)

    # Build body rows
    body_rows = ""
    for _, row in df.iterrows():
        cells = "".join(
            f"<td>{html_module.escape(format_number(row[col]))}</td>" for col in columns
        )
        body_rows += f"<tr>{cells}</tr>"

    interactive_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IMF Presentation Table</title>
    <link rel="stylesheet" href="https://rsms.me/inter/inter.css">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            margin: 0; padding: 20px; background: #1a1a2e; color: #eee;
        }}
        .table-container {{
            max-height: 85vh; overflow: auto; border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        table {{
            width: 100%; border-collapse: collapse; background: #16213e;
        }}
        thead {{ position: sticky; top: 0; z-index: 10; }}
        th {{
            background: linear-gradient(180deg, #1f4068 0%, #162447 100%);
            padding: 12px 8px; text-align: left; font-weight: 600;
            border-bottom: 2px solid #e94560; white-space: nowrap;
            resize: horizontal; overflow: hidden; min-width: 50px;
        }}
        th:first-child {{ width: 400px; }}
        td {{
            padding: 10px 8px; border-bottom: 1px solid #2a2a4a;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px; max-width: 0;
        }}
        td:first-child {{ white-space: pre; }}
        tr:nth-child(even) {{ background: #1a1a3e; }}
        tr:nth-child(odd) {{ background: #16213e; }}
        tr:hover {{ background: #252560; }}
        /* Scrollbar styling */
        .table-container::-webkit-scrollbar {{ width: 6px; height: 10px; }}
        .table-container::-webkit-scrollbar-track {{ background: #1a1a2e; }}
        .table-container::-webkit-scrollbar-thumb {{
            background: #444; border-radius: 5px;
        }}
        .table-container::-webkit-scrollbar-thumb:hover {{ background: #555; }}
    </style>
</head>
<body>
    <div class="table-container">
        <table id="dataTable">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{body_rows}</tbody>
        </table>
    </div>
</body>
</html>"""

    return HTMLResponse(content=interactive_html)