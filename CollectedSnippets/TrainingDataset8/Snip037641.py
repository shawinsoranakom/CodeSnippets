def get_label_visibility_proto_value(
    label_visibility_string: type_util.LabelVisibility,
) -> LabelVisibilityMessage.LabelVisibilityOptions.ValueType:
    """Returns one of LabelVisibilityMessage enum constants based on string value."""

    if label_visibility_string == "visible":
        return LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE
    elif label_visibility_string == "hidden":
        return LabelVisibilityMessage.LabelVisibilityOptions.HIDDEN
    elif label_visibility_string == "collapsed":
        return LabelVisibilityMessage.LabelVisibilityOptions.COLLAPSED

    raise ValueError(f"Unknown label visibility value: {label_visibility_string}")