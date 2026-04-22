def register_file_change_callback(self, cb: Callable[[str], None]) -> None:
        self._on_file_changed.append(cb)