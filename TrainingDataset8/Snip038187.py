def register_widget(
    element_type: ElementType,
    element_proto: WidgetProto,
    deserializer: WidgetDeserializer[T],
    serializer: WidgetSerializer[T],
    ctx: Optional["ScriptRunContext"],
    user_key: Optional[str] = None,
    widget_func_name: Optional[str] = None,
    on_change_handler: Optional[WidgetCallback] = None,
    args: Optional[WidgetArgs] = None,
    kwargs: Optional[WidgetKwargs] = None,
) -> RegisterWidgetResult[T]:
    """Register a widget with Streamlit, and return its current value.
    NOTE: This function should be called after the proto has been filled.

    Parameters
    ----------
    element_type : ElementType
        The type of the element as stored in proto.
    element_proto : WidgetProto
        The proto of the specified type (e.g. Button/Multiselect/Slider proto)
    deserializer : WidgetDeserializer[T]
        Called to convert a widget's protobuf value to the value returned by
        its st.<widget_name> function.
    serializer : WidgetSerializer[T]
        Called to convert a widget's value to its protobuf representation.
    ctx : Optional[ScriptRunContext]
        Used to ensure uniqueness of widget IDs, and to look up widget values.
    user_key : Optional[str]
        Optional user-specified string to use as the widget ID.
        If this is None, we'll generate an ID by hashing the element.
    widget_func_name : Optional[str]
        The widget's DeltaGenerator function name, if it's different from
        its element_type. Custom components are a special case: they all have
        the element_type "component_instance", but are instantiated with
        dynamically-named functions.
    on_change_handler : Optional[WidgetCallback]
        An optional callback invoked when the widget's value changes.
    args : Optional[WidgetArgs]
        args to pass to on_change_handler when invoked
    kwargs : Optional[WidgetKwargs]
        kwargs to pass to on_change_handler when invoked

    Returns
    -------
    register_widget_result : RegisterWidgetResult[T]
        Provides information on which value to return to the widget caller,
        and whether the UI needs updating.

        - Unhappy path:
            - Our ScriptRunContext doesn't exist (meaning that we're running
            as a "bare script" outside streamlit).
            - We are disconnected from the SessionState instance.
            In both cases we'll return a fallback RegisterWidgetResult[T].
        - Happy path:
            - The widget has already been registered on a previous run but the
            user hasn't interacted with it on the client. The widget will have
            the default value it was first created with. We then return a
            RegisterWidgetResult[T], containing this value.
            - The widget has already been registered and the user *has*
            interacted with it. The widget will have that most recent
            user-specified value. We then return a RegisterWidgetResult[T],
            containing this value.

        For both paths a widget return value is provided, allowing the widgets
        to be used in a non-streamlit setting.
    """
    widget_id = _get_widget_id(element_type, element_proto, user_key)
    element_proto.id = widget_id

    # Create the widget's updated metadata, and register it with session_state.
    metadata = WidgetMetadata(
        widget_id,
        deserializer,
        serializer,
        value_type=ELEMENT_TYPE_TO_VALUE_TYPE[element_type],
        callback=on_change_handler,
        callback_args=args,
        callback_kwargs=kwargs,
    )
    return register_widget_from_metadata(metadata, ctx, widget_func_name, element_type)