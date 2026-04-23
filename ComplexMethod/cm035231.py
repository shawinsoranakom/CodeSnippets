async def _find_running_sandbox_for_user(self) -> SandboxInfo | None:
        """Find a running sandbox for the current user based on the grouping strategy.

        Returns:
            SandboxInfo if a running sandbox is found, None otherwise.
        """
        try:
            user_id = await self.user_context.get_user_id()
            sandbox_grouping_strategy = await self._get_sandbox_grouping_strategy()

            # If no grouping, return None to force creation of a new sandbox
            if sandbox_grouping_strategy == SandboxGroupingStrategy.NO_GROUPING:
                return None

            # Collect all running sandboxes for this user
            running_sandboxes = []
            page_id = None
            while True:
                page = await self.sandbox_service.search_sandboxes(
                    page_id=page_id, limit=100
                )

                for sandbox in page.items:
                    if (
                        sandbox.status == SandboxStatus.RUNNING
                        and sandbox.created_by_user_id == user_id
                    ):
                        running_sandboxes.append(sandbox)

                if page.next_page_id is None:
                    break
                page_id = page.next_page_id

            if not running_sandboxes:
                return None

            # Apply the grouping strategy
            return await self._select_sandbox_by_strategy(
                running_sandboxes, sandbox_grouping_strategy
            )

        except Exception as e:
            _logger.warning(
                f'Error finding running sandbox for user: {e}', exc_info=True
            )
            return None