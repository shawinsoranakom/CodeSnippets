async def close(self):
        """Close all browser resources and clean up."""
        # Cached CDP path: only clean up this instance's sessions/contexts,
        # then release the shared connection reference.
        if self._using_cached_cdp:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.kill_session(session_id)
            for ctx in self.contexts_by_config.values():
                try:
                    await ctx.close()
                except Exception:
                    pass
            self.contexts_by_config.clear()
            self._context_refcounts.clear()
            self._context_last_used.clear()
            self._page_to_sig.clear()
            await _CDPConnectionCache.release(self.config.cdp_url)
            self.browser = None
            self.playwright = None
            self._using_cached_cdp = False
            return

        if self.config.cdp_url:
            # When using external CDP, we don't own the browser process.
            # If cdp_cleanup_on_close is True, properly disconnect from the browser
            # and clean up Playwright resources. This frees the browser for other clients.
            if self.config.cdp_cleanup_on_close:
                # First close all sessions (pages)
                session_ids = list(self.sessions.keys())
                for session_id in session_ids:
                    await self.kill_session(session_id)

                # Close all contexts we created
                for ctx in self.contexts_by_config.values():
                    try:
                        await ctx.close()
                    except Exception:
                        pass
                self.contexts_by_config.clear()
                self._context_refcounts.clear()
                self._context_last_used.clear()
                self._page_to_sig.clear()

                # Disconnect from browser (doesn't terminate it, just releases connection)
                if self.browser:
                    try:
                        await self.browser.close()
                    except Exception as e:
                        if self.logger:
                            self.logger.debug(
                                message="Error disconnecting from CDP browser: {error}",
                                tag="BROWSER",
                                params={"error": str(e)}
                            )
                    self.browser = None
                    # Allow time for CDP connection to fully release before another client connects
                    if self.config.cdp_close_delay > 0:
                        await asyncio.sleep(self.config.cdp_close_delay)

                # Stop Playwright instance to prevent memory leaks
                if self.playwright:
                    await self.playwright.stop()
                    self.playwright = None
            return

        # ── Persistent context launched via launch_persistent_context ──
        if self._launched_persistent:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.kill_session(session_id)
            for ctx in self.contexts_by_config.values():
                try:
                    await ctx.close()
                except Exception:
                    pass
            self.contexts_by_config.clear()
            self._context_refcounts.clear()
            self._context_last_used.clear()
            self._page_to_sig.clear()

            # Closing the persistent context also terminates the browser
            if self.default_context:
                try:
                    await self.default_context.close()
                except Exception:
                    pass
                self.default_context = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            self._launched_persistent = False
            return

        if self.config.sleep_on_close:
            await asyncio.sleep(0.5)

        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.kill_session(session_id)

        # Now close all contexts we created. This reclaims memory from ephemeral contexts.
        for ctx in self.contexts_by_config.values():
            try:
                await ctx.close()
            except Exception as e:
                self.logger.error(
                    message="Error closing context: {error}",
                    tag="ERROR",
                    params={"error": str(e)}
                )
        self.contexts_by_config.clear()
        self._context_refcounts.clear()
        self._context_last_used.clear()
        self._page_to_sig.clear()

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.managed_browser:
            await asyncio.sleep(0.5)
            await self.managed_browser.cleanup()
            self.managed_browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None