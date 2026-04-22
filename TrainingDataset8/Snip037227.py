def _marshall_uuid(proto, styler, default_uuid):
    """Marshall pandas.Styler UUID into an ArrowTable proto.

    Parameters
    ----------
    proto : proto.ArrowTable
        Output. The protobuf for a Streamlit ArrowTable proto.

    styler : pandas.Styler
        Styler holding styling data for the dataframe.

    default_uuid : str
        If Styler custom uuid is not provided, this value will be used.

    """
    if styler.uuid is None:
        styler.set_uuid(default_uuid)

    proto.styler.uuid = str(styler.uuid)