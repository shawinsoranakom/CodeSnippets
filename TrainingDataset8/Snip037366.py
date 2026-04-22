def _marshall_uuid(proto: ArrowProto, styler: Styler, default_uuid: str) -> None:
    """Marshall pandas.Styler uuid into an Arrow proto.

    Parameters
    ----------
    proto : proto.Arrow
        Output. The protobuf for Streamlit Arrow proto.

    styler : pandas.Styler
        Helps style a DataFrame or Series according to the data with HTML and CSS.

    default_uuid : str
        If pandas.Styler uuid is not provided, this value will be used.

    """
    if styler.uuid is None:
        styler.set_uuid(default_uuid)

    proto.styler.uuid = str(styler.uuid)