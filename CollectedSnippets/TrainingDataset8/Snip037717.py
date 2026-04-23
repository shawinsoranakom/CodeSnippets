def _on_secrets_file_changed(self, _) -> None:
        """Called when `secrets._file_change_listener` emits a Signal."""

        # NOTE: At the time of writing, this function only calls `_on_source_file_changed`.
        # The reason behind creating this function instead of just passing `_on_source_file_changed`
        # to `connect` / `disconnect` directly is that every function that is passed to `connect` / `disconnect`
        # must have at least one argument for `sender` (in this case we don't really care about it, thus `_`),
        # and introducing an unnecessary argument to `_on_source_file_changed` just for this purpose sounded finicky.
        self._on_source_file_changed()