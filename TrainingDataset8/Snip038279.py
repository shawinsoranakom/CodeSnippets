def maybe_raise_label_warnings(label: Optional[str], label_visibility: Optional[str]):
    if not label:
        _LOGGER.warning(
            "`label` got an empty value. This is discouraged for accessibility "
            "reasons and may be disallowed in the future by raising an exception. "
            "Please provide a non-empty label and hide it with label_visibility "
            "if needed."
        )
    if label_visibility not in ("visible", "hidden", "collapsed"):
        raise errors.StreamlitAPIException(
            f"Unsupported label_visibility option '{label_visibility}'. "
            f"Valid values are 'visible', 'hidden' or 'collapsed'."
        )