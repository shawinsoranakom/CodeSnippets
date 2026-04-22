def test_register_pages_changed_callback(self):
        callback = lambda: None

        disconnect = source_util.register_pages_changed_callback(callback)

        source_util._on_pages_changed.connect.assert_called_once_with(
            callback, weak=False
        )

        disconnect()
        source_util._on_pages_changed.disconnect.assert_called_once_with(callback)