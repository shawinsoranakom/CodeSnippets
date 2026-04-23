def _queue_update(
        self, path: str, operation: str, contents: str | bytes | None
    ) -> None:
        """Queue an update to be sent to the webhook.

        Args:
            path: The path that was modified
            operation: The operation performed ("write" or "delete")
            contents: The contents that were written (None for delete operations)
        """
        with self._batch_lock:
            # Calculate content size
            content_size = 0
            if contents is not None:
                if isinstance(contents, str):
                    content_size = len(contents.encode('utf-8'))
                else:
                    content_size = len(contents)

            # Update batch size calculation
            # If this path already exists in the batch, subtract its previous size
            if path in self._batch:
                prev_op, prev_contents = self._batch[path]
                if prev_contents is not None:
                    if isinstance(prev_contents, str):
                        self._batch_size -= len(prev_contents.encode('utf-8'))
                    else:
                        self._batch_size -= len(prev_contents)

            # Add new content size
            self._batch_size += content_size

            # Add to batch
            self._batch[path] = (operation, contents)

            # Check if we need to send the batch due to size limit
            if self._batch_size >= self.batch_size_limit_bytes:
                self._enqueue_batch_from_lock()
                return

            # Start or reset the timer for sending the batch
            if self._batch_timer is not None:
                self._batch_timer.cancel()
                self._batch_timer = None

            timer = threading.Timer(
                self.batch_timeout_seconds, self._enqueue_batch_from_timer
            )
            timer.daemon = True
            timer.start()
            self._batch_timer = timer