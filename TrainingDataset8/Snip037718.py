def _on_pages_changed(self, _) -> None:
        # TODO: Double-check the product behavior we want on this. In the spec,
        # it says that we should notify the client of a pages dir change only
        # if "run on save" is true, but I feel like always sending updates is
        # quite reasonable behavior since the pages nav updating is not
        # potentially disruptive like a script rerunning is.
        msg = ForwardMsg()
        _populate_app_pages(msg.pages_changed, self._session_data.main_script_path)
        self._enqueue_forward_msg(msg)