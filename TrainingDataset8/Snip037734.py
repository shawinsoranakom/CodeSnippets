def save_widget_metadata(metadata: WidgetMetadata[Any]) -> None:
    """Save a widget's metadata to a thread-local callstack, so the widget
    can be registered again when that widget is replayed.
    """
    MEMO_MESSAGE_CALL_STACK.save_widget_metadata(metadata)
    SINGLETON_MESSAGE_CALL_STACK.save_widget_metadata(metadata)