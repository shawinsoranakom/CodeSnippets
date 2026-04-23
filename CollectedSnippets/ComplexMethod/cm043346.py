async def _maybe_cleanup_old_browser(self, sig: str):
        """Clean up an old browser's context if its refcount hit 0 and it's pending cleanup."""
        async with self._pending_cleanup_lock:
            if sig not in self._pending_cleanup:
                return  # Not an old browser signature

            cleanup_info = self._pending_cleanup.pop(sig)
            old_version = cleanup_info["version"]

            if self.logger:
                self.logger.debug(
                    message="Cleaning up context from browser version {version} (sig: {sig})",
                    tag="BROWSER",
                    params={"version": old_version, "sig": sig[:12]},
                )

            # Remove context from tracking
            async with self._contexts_lock:
                context = self.contexts_by_config.pop(sig, None)
                self._context_refcounts.pop(sig, None)
                self._context_last_used.pop(sig, None)

            # Close context outside locks
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass

            # Check if any signatures from this old version remain
            remaining_old = [
                s for s, info in self._pending_cleanup.items()
                if info["version"] == old_version
            ]

            if not remaining_old:
                if self.logger:
                    self.logger.info(
                        message="All contexts from browser version {version} cleaned up",
                        tag="BROWSER",
                        params={"version": old_version},
                    )

            # Open a cleanup slot if we're below the cap
            if len(self._pending_cleanup) < self._max_pending_browsers:
                self._cleanup_slot_available.set()