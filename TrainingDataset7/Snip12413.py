def _live_receivers(self, sender):
        """
        Filter sequence of receivers to get resolved, live receivers.

        This checks for weak references and resolves them, then returning only
        live receivers.
        """
        receivers = None
        if self.use_caching and not self._dead_receivers:
            receivers = self.sender_receivers_cache.get(sender)
            # We could end up here with NO_RECEIVERS even if we do check this
            # case in .send() prior to calling _live_receivers() due to
            # concurrent .send() call.
            if receivers is NO_RECEIVERS:
                return [], []
        if receivers is None:
            with self.lock:
                self._clear_dead_receivers()
                senderkey = _make_id(sender)
                receivers = []
                for (
                    (_receiverkey, r_senderkey),
                    receiver,
                    sender_ref,
                    is_async,
                ) in self.receivers:
                    if r_senderkey == NONE_ID or r_senderkey == senderkey:
                        receivers.append((receiver, sender_ref, is_async))
                if self.use_caching:
                    if not receivers:
                        self.sender_receivers_cache[sender] = NO_RECEIVERS
                    else:
                        # Note, we must cache the weakref versions.
                        self.sender_receivers_cache[sender] = receivers
        non_weak_sync_receivers = []
        non_weak_async_receivers = []
        for receiver, sender_ref, is_async in receivers:
            # Skip if the receiver/sender is a dead weakref
            if isinstance(receiver, weakref.ReferenceType):
                receiver = receiver()
                if receiver is None:
                    continue
            if sender_ref is not None and sender_ref() is None:
                continue
            if is_async:
                non_weak_async_receivers.append(receiver)
            else:
                non_weak_sync_receivers.append(receiver)
        return non_weak_sync_receivers, non_weak_async_receivers