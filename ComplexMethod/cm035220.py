async def pause_old_sandboxes(self, max_num_sandboxes: int) -> list[str]:
        """Pause the oldest sandboxes if there are more than max_num_sandboxes running.
        In a multi user environment, this will pause sandboxes only for the current user.

        Args:
            max_num_sandboxes: Maximum number of sandboxes to keep running

        Returns:
            List of sandbox IDs that were paused
        """
        if max_num_sandboxes <= 0:
            raise ValueError('max_num_sandboxes must be greater than 0')

        # Get all running sandboxes (iterate through all pages)
        running_sandboxes = []
        async for sandbox in page_iterator(self.search_sandboxes, limit=100):
            if sandbox.status == SandboxStatus.RUNNING:
                running_sandboxes.append(sandbox)

        # If we're within the limit, no cleanup needed
        if len(running_sandboxes) <= max_num_sandboxes:
            return []

        # Sort by creation time (oldest first)
        running_sandboxes.sort(key=lambda x: x.created_at)

        # Determine how many to pause
        num_to_pause = len(running_sandboxes) - max_num_sandboxes
        sandboxes_to_pause = running_sandboxes[:num_to_pause]

        # Stop the oldest sandboxes
        paused_sandbox_ids = []
        for sandbox in sandboxes_to_pause:
            try:
                success = await self.pause_sandbox(sandbox.id)
                if success:
                    paused_sandbox_ids.append(sandbox.id)
            except Exception:
                # Continue trying to pause other sandboxes even if one fails
                pass

        return paused_sandbox_ids