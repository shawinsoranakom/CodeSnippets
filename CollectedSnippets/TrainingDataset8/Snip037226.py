def _marshall_styler(proto, styler, default_uuid):
    """Marshall pandas.Styler styling data into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    styler : pandas.Styler
        Styler holding styling data for the dataframe.

    default_uuid : str
        If Styler custom uuid is not provided, this value will be used.

    """
    # NB: UUID should be set before _compute is called.
    _marshall_uuid(proto, styler, default_uuid)

    # NB: We're using protected members of Styler to get styles,
    # which is non-ideal and could break if Styler's interface changes.
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