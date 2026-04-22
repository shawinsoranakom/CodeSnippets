def _get_widget_id(
    element_type: str, element_proto: WidgetProto, user_key: Optional[str] = None
) -> str:
    """Generate a widget id for the given widget.

    The widget id includes the user_key so widgets with identical arguments can
    use it to be distinct.

    The widget id includes an easily identified prefix, and the user_key as a
    suffix, to make it easy to identify it and know if a key maps to it.

    Does not mutate the element_proto object.
    """
    h = hashlib.new("md5")
    h.update(element_type.encode("utf-8"))
    h.update(element_proto.SerializeToString())
    return f"{GENERATED_WIDGET_KEY_PREFIX}-{h.hexdigest()}-{user_key}"