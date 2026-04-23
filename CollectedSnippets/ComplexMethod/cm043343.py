async def _get_page_by_target_id(self, context: BrowserContext, target_id: str):
        """
        Get an existing page by its CDP target ID.

        This is used when connecting to a pre-created browser context with an existing page.
        Playwright may not immediately see targets created via raw CDP commands, so we
        use CDP to get all targets and find the matching one.

        Args:
            context: The browser context to search in
            target_id: The CDP target ID to find

        Returns:
            Page object if found, None otherwise
        """
        try:
            # First check if Playwright already sees the page
            for page in context.pages:
                # Playwright's internal target ID might match
                if hasattr(page, '_impl_obj') and hasattr(page._impl_obj, '_target_id'):
                    if page._impl_obj._target_id == target_id:
                        return page

            # If not found, try using CDP to get targets
            if hasattr(self.browser, '_impl_obj') and hasattr(self.browser._impl_obj, '_connection'):
                cdp_session = await context.new_cdp_session(context.pages[0] if context.pages else None)
                if cdp_session:
                    try:
                        result = await cdp_session.send("Target.getTargets")
                        targets = result.get("targetInfos", [])
                        for target in targets:
                            if target.get("targetId") == target_id:
                                # Found the target - if it's a page type, we can use it
                                if target.get("type") == "page":
                                    # The page exists, let Playwright discover it
                                    await asyncio.sleep(0.1)
                                    # Refresh pages list
                                    if context.pages:
                                        return context.pages[0]
                    finally:
                        await cdp_session.detach()

            # Fallback: if there are any pages now, return the first one
            if context.pages:
                return context.pages[0]

            return None
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    message="Failed to get page by target ID: {error}",
                    tag="BROWSER",
                    params={"error": str(e)}
                )
            return None