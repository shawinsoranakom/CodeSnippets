def register_widget_from_metadata(
    metadata: WidgetMetadata[T],
    ctx: Optional["ScriptRunContext"],
    widget_func_name: Optional[str],
    element_type: ElementType,
) -> RegisterWidgetResult[T]:
    """Register a widget and return its value, using an already constructed
    `WidgetMetadata`.

    This is split out from `register_widget` to allow caching code to replay
    widgets by saving and reusing the completed metadata.

    See `register_widget` for details on what this returns.
    """
    # Local import to avoid import cycle
    import streamlit.runtime.caching as caching

    if ctx is None:
        # Early-out if we don't have a script run context (which probably means
        # we're running as a "bare" Python script, and not via `streamlit run`).
        return RegisterWidgetResult.failure(deserializer=metadata.deserializer)

    widget_id = metadata.id
    user_key = user_key_from_widget_id(widget_id)

    # Ensure another widget with the same user key hasn't already been registered.
    if user_key is not None:
        if user_key not in ctx.widget_user_keys_this_run:
            ctx.widget_user_keys_this_run.add(user_key)
        else:
            raise DuplicateWidgetID(
                _build_duplicate_widget_message(
                    widget_func_name if widget_func_name is not None else element_type,
                    user_key,
                )
            )

    # Ensure another widget with the same id hasn't already been registered.
    new_widget = widget_id not in ctx.widget_ids_this_run
    if new_widget:
        ctx.widget_ids_this_run.add(widget_id)
    else:
        raise DuplicateWidgetID(
            _build_duplicate_widget_message(
                widget_func_name if widget_func_name is not None else element_type,
                user_key,
            )
        )
    # Save the widget metadata for cached result replay
    caching.save_widget_metadata(metadata)
    return ctx.session_state.register_widget(metadata, user_key)