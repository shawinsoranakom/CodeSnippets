async def _maybe_bump_browser_version(self):
        """Bump browser version if threshold reached, moving old browser to pending cleanup.

        New requests automatically get a new browser (via new signature).
        Old browser drains naturally and gets cleaned up when refcount hits 0.
        """
        if not self._should_recycle():
            return

        # Safety cap: wait if too many old browsers are draining
        while True:
            async with self._pending_cleanup_lock:
                # Re-check threshold under lock (another request may have bumped already)
                if not self._should_recycle():
                    return

                # Check safety cap
                if len(self._pending_cleanup) >= self._max_pending_browsers:
                    if self.logger:
                        self.logger.debug(
                            message="Waiting for old browser to drain (pending: {count})",
                            tag="BROWSER",
                            params={"count": len(self._pending_cleanup)},
                        )
                    self._cleanup_slot_available.clear()
                    # Release lock and wait
                else:
                    # We have a slot — do the bump inside this lock hold
                    old_version = self._browser_version
                    active_sigs = []
                    idle_sigs = []
                    async with self._contexts_lock:
                        for sig in list(self._context_refcounts.keys()):
                            if self._context_refcounts.get(sig, 0) > 0:
                                active_sigs.append(sig)
                            else:
                                idle_sigs.append(sig)

                    if self.logger:
                        self.logger.info(
                            message="Bumping browser version {old} -> {new} after {count} pages ({active} active, {idle} idle sigs)",
                            tag="BROWSER",
                            params={
                                "old": old_version,
                                "new": old_version + 1,
                                "count": self._pages_served,
                                "active": len(active_sigs),
                                "idle": len(idle_sigs),
                            },
                        )

                    # Only add sigs with active crawls to pending cleanup.
                    # Sigs with refcount 0 are cleaned up immediately below
                    # to avoid them being stuck in _pending_cleanup forever
                    # (no future release would trigger their cleanup).
                    done_event = asyncio.Event()
                    for sig in active_sigs:
                        self._pending_cleanup[sig] = {
                            "version": old_version,
                            "done": done_event,
                        }

                    # Bump version — new get_page() calls will create new contexts
                    self._browser_version += 1
                    self._pages_served = 0

                    # Clean up idle sigs immediately (outside pending_cleanup_lock below)
                    break  # exit while loop to do cleanup outside locks

            # Safety cap path: wait for a cleanup slot, then retry.
            # Timeout prevents permanent deadlock if stuck entries never drain.
            try:
                await asyncio.wait_for(
                    self._cleanup_slot_available.wait(), timeout=30.0
                )
            except asyncio.TimeoutError:
                # Force-clean any pending entries that have refcount 0
                # (they're stuck and will never drain naturally)
                async with self._pending_cleanup_lock:
                    stuck_sigs = [
                        s for s in list(self._pending_cleanup.keys())
                        if self._context_refcounts.get(s, 0) == 0
                    ]
                    for sig in stuck_sigs:
                        self._pending_cleanup.pop(sig, None)
                    if stuck_sigs:
                        if self.logger:
                            self.logger.warning(
                                message="Force-cleaned {count} stuck pending entries after timeout",
                                tag="BROWSER",
                                params={"count": len(stuck_sigs)},
                            )
                        # Clean up the stuck contexts
                        for sig in stuck_sigs:
                            async with self._contexts_lock:
                                context = self.contexts_by_config.pop(sig, None)
                                self._context_refcounts.pop(sig, None)
                                self._context_last_used.pop(sig, None)
                            if context is not None:
                                try:
                                    await context.close()
                                except Exception:
                                    pass
                        if len(self._pending_cleanup) < self._max_pending_browsers:
                            self._cleanup_slot_available.set()

        # Reached via break — clean up idle sigs immediately (outside locks)
        for sig in idle_sigs:
            async with self._contexts_lock:
                context = self.contexts_by_config.pop(sig, None)
                self._context_refcounts.pop(sig, None)
                self._context_last_used.pop(sig, None)
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
        if idle_sigs and self.logger:
            self.logger.debug(
                message="Immediately cleaned up {count} idle contexts from version {version}",
                tag="BROWSER",
                params={"count": len(idle_sigs), "version": old_version},
            )