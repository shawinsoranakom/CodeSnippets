def _download_threaded(self, *e):
        # If the user tries to start a new download while we're already
        # downloading something, then abort the current download instead.
        if self._downloading:
            self._abort_download()
            return

        # Change the 'download' button to an 'abort' button.
        self._download_button["text"] = "Cancel"

        marked = [
            self._table[row, "Identifier"]
            for row in range(len(self._table))
            if self._table[row, 0] != ""
        ]
        selection = self._table.selected_row()
        if not marked and selection is not None:
            marked = [self._table[selection, "Identifier"]]

        # Create a new data server object for the download operation,
        # just in case the user modifies our data server during the
        # download (e.g., clicking 'refresh' or editing the index url).
        ds = Downloader(self._ds.url, self._ds.download_dir)

        # Start downloading in a separate thread.
        assert self._download_msg_queue == []
        assert self._download_abort_queue == []
        self._DownloadThread(
            ds,
            marked,
            self._download_lock,
            self._download_msg_queue,
            self._download_abort_queue,
        ).start()

        # Monitor the download message queue & display its progress.
        self._log_indent = 0
        self._downloading = True
        self._monitor_message_queue()

        # Display an indication that we're still alive and well by
        # cycling the progress bar.
        self._progress_alive()