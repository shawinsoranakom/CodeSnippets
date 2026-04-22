def _marshall_styler(proto: ArrowProto, styler: Styler, default_uuid: str) -> None:
    """Marshall pandas.Styler into an Arrow proto.

    Parameters
    ----------
    proto : proto.Arrow
        Output. The protobuf for Streamlit Arrow proto.

    styler : pandas.Styler
        Helps style a DataFrame or Series according to the data with HTML and CSS.

    default_uuid : str
        If pandas.Styler uuid is not provided, this value will be used.

    """
    # pandas.Styler uuid should be set before _compute is called.
    _marshall_uuid(proto, styler, default_uuid)

    # We're using protected members of pandas.Styler to get styles,
    # which is not ideal and could break if the interface changes.
    styler._compute()

    # In Pandas 1.3.0, styler._translate() signature was changed.
    # 2 arguments were added: sparse_index and sparse_columns.
    # The functionality that they provide is not yet supported.
    if type_util.is_pandas_version_less_than("1.3.0"):
        pandas_styles = styler._translate()
    else:
        pandas_styles = styler._translate(False, False)

    _marshall_caption(proto, styler)
    _marshall_styles(proto, styler, pandas_styles)
    _marshall_display_values(proto, styler.data, pandas_styles)