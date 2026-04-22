def register_pages_changed_callback(
    callback: Callable[[str], None],
):
    def disconnect():
        _on_pages_changed.disconnect(callback)

    # weak=False so that we have control of when the pages changed
    # callback is deregistered.
    _on_pages_changed.connect(callback, weak=False)

    return disconnect