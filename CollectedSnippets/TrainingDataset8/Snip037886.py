def enqueue(self, msg: ForwardMsg) -> None:
        """Add message into queue, possibly composing it with another message."""
        if not _is_composable_message(msg):
            self._queue.append(msg)
            return

        # If there's a Delta message with the same delta_path already in
        # the queue - meaning that it refers to the same location in
        # the app - we attempt to combine this new Delta into the old
        # one. This is an optimization that prevents redundant Deltas
        # from being sent to the frontend.
        delta_key = tuple(msg.metadata.delta_path)
        if delta_key in self._delta_index_map:
            index = self._delta_index_map[delta_key]
            old_msg = self._queue[index]
            composed_delta = _maybe_compose_deltas(old_msg.delta, msg.delta)
            if composed_delta is not None:
                new_msg = ForwardMsg()
                new_msg.delta.CopyFrom(composed_delta)
                new_msg.metadata.CopyFrom(msg.metadata)
                self._queue[index] = new_msg
                return

        # No composition occurred. Append this message to the queue, and
        # store its index for potential future composition.
        self._delta_index_map[delta_key] = len(self._queue)
        self._queue.append(msg)