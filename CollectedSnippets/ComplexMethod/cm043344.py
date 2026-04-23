async def get_page(self, crawlerRunConfig: CrawlerRunConfig):
        """
        Get a page for the given session ID, creating a new one if needed.

        Args:
            crawlerRunConfig (CrawlerRunConfig): Configuration object containing all browser settings

        Returns:
            (page, context): The Page and its BrowserContext
        """
        self._cleanup_expired_sessions()

        # If a session_id is provided and we already have it, reuse that page + context
        if crawlerRunConfig.session_id and crawlerRunConfig.session_id in self.sessions:
            context, page, _ = self.sessions[crawlerRunConfig.session_id]
            # Update last-used timestamp
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            return page, context

        # If using a managed browser, just grab the shared default_context
        if self.config.use_managed_browser:
            # If create_isolated_context is True, create isolated contexts for concurrent crawls
            # Uses the same caching mechanism as non-CDP mode: cache context by config signature,
            # but always create a new page. This prevents navigation conflicts while allowing
            # context reuse for multiple URLs with the same config (e.g., batch/deep crawls).
            if self.config.create_isolated_context:
                config_signature = self._make_config_signature(crawlerRunConfig)
                to_close = None

                async with self._contexts_lock:
                    if config_signature in self.contexts_by_config:
                        context = self.contexts_by_config[config_signature]
                    else:
                        context = await self.create_browser_context(crawlerRunConfig)
                        await self.setup_context(context, crawlerRunConfig)
                        self.contexts_by_config[config_signature] = context
                        self._context_refcounts[config_signature] = 0
                        to_close = self._evict_lru_context_locked()

                    # Increment refcount INSIDE lock before releasing
                    self._context_refcounts[config_signature] = (
                        self._context_refcounts.get(config_signature, 0) + 1
                    )
                    self._context_last_used[config_signature] = time.monotonic()

                # Close evicted context OUTSIDE lock
                if to_close is not None:
                    try:
                        await to_close.close()
                    except Exception:
                        pass

                # Always create a new page for each crawl (isolation for navigation)
                try:
                    page = await context.new_page()
                except Exception:
                    async with self._contexts_lock:
                        if config_signature in self._context_refcounts:
                            self._context_refcounts[config_signature] = max(
                                0, self._context_refcounts[config_signature] - 1
                            )
                    raise
                await self._apply_stealth_to_page(page)
                self._page_to_sig[page] = config_signature
            elif self.config.storage_state:
                tmp_context = await self.create_browser_context(crawlerRunConfig)
                ctx = self.default_context        # default context, one window only
                ctx = await clone_runtime_state(tmp_context, ctx, crawlerRunConfig, self.config)
                # Close the temporary context — only needed as a clone source
                try:
                    await tmp_context.close()
                except Exception:
                    pass
                context = ctx  # so (page, context) return value is correct
                # Avoid concurrent new_page on shared persistent context
                # See GH-1198: context.pages can be empty under races
                async with self._page_lock:
                    page = await ctx.new_page()
                await self._apply_stealth_to_page(page)
            else:
                context = self.default_context

                # Handle pre-existing target case (for reconnecting to specific CDP targets)
                if self.config.browser_context_id and self.config.target_id:
                    page = await self._get_page_by_target_id(context, self.config.target_id)
                    if not page:
                        async with self._page_lock:
                            page = await context.new_page()
                            self._mark_page_in_use(page)
                        await self._apply_stealth_to_page(page)
                    else:
                        # Mark pre-existing target as in use
                        self._mark_page_in_use(page)
                else:
                    # For CDP connections (external browser), multiple Playwright connections
                    # create separate browser/context objects. Page reuse across connections
                    # isn't reliable because each connection sees different page objects.
                    # Always create new pages for CDP to avoid cross-connection race conditions.
                    if self.config.cdp_url and not self.config.use_managed_browser:
                        async with self._page_lock:
                            page = await context.new_page()
                            self._mark_page_in_use(page)
                        await self._apply_stealth_to_page(page)
                    else:
                        # For managed browsers (single process), page reuse is safe.
                        # Use lock to safely check for available pages and track usage.
                        # This prevents race conditions when multiple crawls run concurrently.
                        async with BrowserManager._get_global_lock():
                            pages = context.pages
                            pages_in_use = self._get_pages_in_use()
                            # Find first available page (exists and not currently in use)
                            available_page = next(
                                (p for p in pages if p not in pages_in_use),
                                None
                            )
                            if available_page:
                                page = available_page
                            else:
                                # No available pages - create a new one
                                page = await context.new_page()
                                await self._apply_stealth_to_page(page)
                            # Mark page as in use (global tracking)
                            self._mark_page_in_use(page)
        else:
            # Otherwise, check if we have an existing context for this config
            config_signature = self._make_config_signature(crawlerRunConfig)
            to_close = None

            async with self._contexts_lock:
                if config_signature in self.contexts_by_config:
                    context = self.contexts_by_config[config_signature]
                else:
                    # Create and setup a new context
                    context = await self.create_browser_context(crawlerRunConfig)
                    await self.setup_context(context, crawlerRunConfig)
                    self.contexts_by_config[config_signature] = context
                    self._context_refcounts[config_signature] = 0
                    to_close = self._evict_lru_context_locked()

                # Increment refcount INSIDE lock before releasing
                self._context_refcounts[config_signature] = (
                    self._context_refcounts.get(config_signature, 0) + 1
                )
                self._context_last_used[config_signature] = time.monotonic()

            # Close evicted context OUTSIDE lock
            if to_close is not None:
                try:
                    await to_close.close()
                except Exception:
                    pass

            # Create a new page from the chosen context
            try:
                page = await context.new_page()
            except Exception:
                async with self._contexts_lock:
                    if config_signature in self._context_refcounts:
                        self._context_refcounts[config_signature] = max(
                            0, self._context_refcounts[config_signature] - 1
                        )
                raise
            await self._apply_stealth_to_page(page)
            self._page_to_sig[page] = config_signature

        # If a session_id is specified, store this session so we can reuse later
        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())

        self._pages_served += 1

        # Check if browser recycle threshold is hit — bump version for next requests
        # This happens AFTER incrementing counter so concurrent requests see correct count
        await self._maybe_bump_browser_version()

        return page, context