def _marshall_display_values(proto, df, styles):
    """Marshall pandas.Styler display values into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    df : pandas.DataFrame
        A dataframe with original values.

    styles : dict
        pandas.Styler translated styles.

    """
    new_df = _use_display_values(df, styles)
    proto.styler.display_values = _dataframe_to_pybytes(new_df)