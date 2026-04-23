def _monitor_message_queue(self):
        def show(s):
            self._progresslabel["text"] = s
            self._log(s)

        # Try to acquire the lock; if it's busy, then just try again later.
        if not self._download_lock.acquire():
            return
        for msg in self._download_msg_queue:

            # Done downloading?
            if msg == "finished" or msg == "aborted":
                # self._fill_table(sort=False)
                self._update_table_status()
                self._downloading = False
                self._download_button["text"] = "Download"
                del self._download_msg_queue[:]
                del self._download_abort_queue[:]
                self._download_lock.release()
                if msg == "aborted":
                    show("Download aborted!")
                    self._show_progress(None)
                else:
                    afterid = self.top.after(100, self._show_progress, None)
                    self._afterid["_monitor_message_queue"] = afterid
                return

            # All other messages
            elif isinstance(msg, ProgressMessage):
                self._show_progress(msg.progress)
            elif isinstance(msg, ErrorMessage):
                show(msg.message)
                if msg.package is not None:
                    self._select(msg.package.id)
                self._show_progress(None)
                self._downloading = False
                return  # halt progress.
            elif isinstance(msg, StartCollectionMessage):
                show("Downloading collection %r" % msg.collection.id)
                self._log_indent += 1
            elif isinstance(msg, StartPackageMessage):
                self._ds.clear_status_cache(msg.package.id)
                show("Downloading package %r" % msg.package.id)
            elif isinstance(msg, UpToDateMessage):
                show("Package %s is up-to-date!" % msg.package.id)
            # elif isinstance(msg, StaleMessage):
            #    show('Package %s is out-of-date or corrupt; updating it' %
            #         msg.package.id)
            elif isinstance(msg, FinishDownloadMessage):
                show("Finished downloading %r." % msg.package.id)
            elif isinstance(msg, StartUnzipMessage):
                show("Unzipping %s" % msg.package.filename)
            elif isinstance(msg, FinishUnzipMessage):
                show("Finished installing %s" % msg.package.id)
            elif isinstance(msg, FinishCollectionMessage):
                self._log_indent -= 1
                show("Finished downloading collection %r." % msg.collection.id)
                self._clear_mark(msg.collection.id)
            elif isinstance(msg, FinishPackageMessage):
                self._update_table_status()
                self._clear_mark(msg.package.id)

        # Let the user know when we're aborting a download (but
        # waiting for a good point to abort it, so we don't end up
        # with a partially unzipped package or anything like that).
        if self._download_abort_queue:
            self._progresslabel["text"] = "Aborting download..."

        # Clear the message queue and then release the lock
        del self._download_msg_queue[:]
        self._download_lock.release()

        # Check the queue again after MONITOR_QUEUE_DELAY msec.
        afterid = self.top.after(self._MONITOR_QUEUE_DELAY, self._monitor_message_queue)
        self._afterid["_monitor_message_queue"] = afterid