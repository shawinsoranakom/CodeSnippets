def _marshall_caption(proto, styler):
    """Marshall pandas.Styler caption into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    styler : pandas.Styler
        Styler holding styling data for the dataframe.

    """
    if styler.caption is not None:
        proto.styler.caption = styler.caption