def _dispatcher_loop(self) -> None:
        """Background loop: read resp_queue → route to mailboxes by request_id."""
        while not self._dispatcher_stop.is_set():
            if self._resp_queue is None:
                break

            try:
                resp = self._resp_queue.get(timeout = _DISPATCH_POLL_INTERVAL)
            except queue.Empty:
                continue
            except (EOFError, OSError, ValueError):
                break

            rid = resp.get("request_id")
            rtype = resp.get("type", "")

            # Status messages — log and skip
            if rtype == "status":
                logger.info("Subprocess status: %s", resp.get("message", ""))
                continue

            # Route to mailbox if a matching request_id exists
            if rid:
                with self._mailbox_lock:
                    mbox = self._mailboxes.get(rid)
                if mbox is not None:
                    mbox.put(resp)
                    continue

            # No matching mailbox — might be for a _gen_lock reader or orphaned
            # Push it back so _read_resp can pick it up. But we can't un-get
            # from mp.Queue, so log a warning.
            if rtype not in ("status",):
                logger.debug(
                    "Dispatcher: no mailbox for request_id=%s type=%s, dropping",
                    rid,
                    rtype,
                )