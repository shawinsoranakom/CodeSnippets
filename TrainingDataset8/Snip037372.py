def _use_display_values(df: DataFrame, styles: Mapping[str, Any]) -> DataFrame:
    """Create a new pandas.DataFrame where display values are used instead of original ones.

    Parameters
    ----------
    df : pandas.DataFrame
        A dataframe with original values.

    styles : dict
        pandas.Styler translated styles.

    """
    import re

    # If values in a column are not of the same type, Arrow
    # serialization would fail. Thus, we need to cast all values
    # of the dataframe to strings before assigning them display values.
    new_df = df.astype(str)

    cell_selector_regex = re.compile(r"row(\d+)_col(\d+)")
    if "body" in styles:
        rows = styles["body"]
        for row in rows:
            for cell in row:
                match = cell_selector_regex.match(cell["id"])
                if match:
                    r, c = map(int, match.groups())
                    new_df.iat[r, c] = str(cell["display_value"])

    return new_df