def print_rich_table(  # noqa: PLR0912
    df: pd.DataFrame,
    show_index: bool = False,
    title: str = "",
    index_name: str = "",
    headers: list[str] | pd.Index | None = None,
    floatfmt: str | list[str] = ".2f",
    show_header: bool = True,
    automatic_coloring: bool = False,
    columns_to_auto_color: list[str] | None = None,
    rows_to_auto_color: list[str] | None = None,
    export: bool = False,
    limit: int | None = 1000,
    columns_keep_types: list[str] | None = None,
    use_tabulate_df: bool = True,
):
    """Prepare a table from df in rich.

    Parameters
    ----------
    df: pd.DataFrame
        Dataframe to turn into table
    show_index: bool
        Whether to include index
    title: str
        Title for table
    index_name : str
        Title for index column
    headers: List[str]
        Titles for columns
    floatfmt: Union[str, List[str]]
        Float number formatting specs as string or list of strings. Defaults to ".2f"
    show_header: bool
        Whether to show the header row.
    automatic_coloring: bool
        Automatically color a table based on positive and negative values
    columns_to_auto_color: List[str]
        Columns to automatically color
    rows_to_auto_color: List[str]
        Rows to automatically color
    export: bool
        Whether we are exporting the table to a file. If so, we don't want to print it.
    limit: Optional[int]
        Limit the number of rows to show.
    columns_keep_types: Optional[List[str]]
        Columns to keep their types, i.e. not convert to numeric
    """
    if export:
        return

    MAX_COLS = session.settings.ALLOWED_NUMBER_OF_COLUMNS
    MAX_ROWS = session.settings.ALLOWED_NUMBER_OF_ROWS

    # Make a copy of the dataframe to avoid SettingWithCopyWarning
    df = df.copy()

    show_index = not isinstance(df.index, pd.RangeIndex) and show_index
    #  convert non-str that are not timestamp or int into str
    # eg) praw.models.reddit.subreddit.Subreddit
    for col in df.columns:
        if columns_keep_types is not None and col in columns_keep_types:
            continue
        try:
            if not any(
                isinstance(df[col].iloc[x], pd.Timestamp)
                for x in range(min(10, len(df)))
            ):
                df[col] = df[col].apply(pd.to_numeric)
        except (ValueError, TypeError):
            df[col] = df[col].astype(str)

    def _get_headers(_headers: list[str] | pd.Index) -> list[str]:
        """Check if headers are valid and return them."""
        output = _headers
        if isinstance(_headers, pd.Index):
            output = list(_headers)
        if len(output) != len(df.columns):
            raise ValueError("Length of headers does not match length of DataFrame.")
        return output  # type: ignore

    if session.settings.USE_INTERACTIVE_DF:
        df_outgoing = df.copy()
        # If headers are provided, use them
        if headers is not None:
            # We check if headers are valid
            df_outgoing.columns = _get_headers(headers)

        if show_index and index_name not in df_outgoing.columns:
            # If index name is provided, we use it
            df_outgoing.index.name = index_name or "Index"
            df_outgoing = df_outgoing.reset_index()

        for col in df_outgoing.columns:
            if col == "":
                df_outgoing = df_outgoing.rename(columns={col: "  "})

        session._backend.send_table(  # type: ignore  # pylint: disable=protected-access
            df_table=df_outgoing,
            title=title,
            theme=session.user.preferences.table_style,
        )
        return

    df = df.copy() if not limit else df.copy().iloc[:limit]
    if automatic_coloring:
        if columns_to_auto_color:
            for col in columns_to_auto_color:
                # checks whether column exists
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: return_colored_value(str(x)))
        if rows_to_auto_color:
            for row in rows_to_auto_color:
                # checks whether row exists
                if row in df.index:
                    df.loc[row] = df.loc[row].apply(
                        lambda x: return_colored_value(str(x))
                    )

        if columns_to_auto_color is None and rows_to_auto_color is None:
            df = df.map(lambda x: return_colored_value(str(x)))  # type: ignore

    exceeds_allowed_columns = len(df.columns) > MAX_COLS
    exceeds_allowed_rows = len(df) > MAX_ROWS

    if exceeds_allowed_columns:
        original_columns = df.columns.tolist()
        trimmed_columns = df.columns.tolist()[:MAX_COLS]
        df = df[trimmed_columns]
        trimmed_columns = [
            col for col in original_columns if col not in trimmed_columns
        ]

    if exceeds_allowed_rows:
        n_rows = len(df.index)
        max_rows = MAX_ROWS
        df = df[:max_rows]
        trimmed_rows_count = n_rows - max_rows

    if use_tabulate_df:
        table = Table(title=title, show_lines=True, show_header=show_header)

        if show_index:
            table.add_column(index_name)

        if headers is not None:
            headers = _get_headers(headers)
            for header in headers:
                table.add_column(str(header))
        else:
            for column in df.columns:
                table.add_column(str(column))

        if isinstance(floatfmt, list) and len(floatfmt) != len(df.columns):
            raise (
                ValueError(
                    "Length of floatfmt list does not match length of DataFrame columns."
                )
            )
        if isinstance(floatfmt, str):
            floatfmt = [floatfmt for _ in range(len(df.columns))]

        for idx, values in zip(df.index.tolist(), df.values.tolist()):
            # remove hour/min/sec from timestamp index - Format: YYYY-MM-DD # make better
            row_idx = [str(idx)] if show_index else []
            row_idx += [
                (
                    str(x)
                    if not isinstance(x, float) and not isinstance(x, np.float64)
                    else (
                        f"{x:{floatfmt[idx]}}"
                        if isinstance(floatfmt, list)
                        else (
                            f"{x:.2e}"
                            if 0 < abs(float(x)) <= 0.0001
                            else f"{x:floatfmt}"
                        )
                    )
                )
                for idx, x in enumerate(values)
            ]
            table.add_row(*row_idx)
        session.console.print(table)
    else:
        session.console.print(df.to_string(col_space=0))

    if exceeds_allowed_columns:
        session.console.print(
            f"[yellow]\nAllowed number of columns exceeded ({session.settings.ALLOWED_NUMBER_OF_COLUMNS}).\n"
            f"The following columns were removed from the output: {', '.join(trimmed_columns)}.\n[/yellow]"
        )

    if exceeds_allowed_rows:
        session.console.print(
            f"[yellow]\nAllowed number of rows exceeded ({session.settings.ALLOWED_NUMBER_OF_ROWS}).\n"
            f"{trimmed_rows_count} rows were removed from the output.\n[/yellow]"
        )

    if exceeds_allowed_columns or exceeds_allowed_rows:
        session.console.print(
            "Use the `--export` flag to analyse the full output on a file."
        )