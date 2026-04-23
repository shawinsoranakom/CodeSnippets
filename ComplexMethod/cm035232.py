async def _select_sandbox_by_strategy(
        self,
        running_sandboxes: list[SandboxInfo],
        sandbox_grouping_strategy: SandboxGroupingStrategy,
    ) -> SandboxInfo | None:
        """Select a sandbox from the list based on the configured grouping strategy.

        Args:
            running_sandboxes: List of running sandboxes for the user
            sandbox_grouping_strategy: The strategy to use for selection

        Returns:
            Selected sandbox based on the strategy, or None if no sandbox is available
            (e.g., all sandboxes have reached max_num_conversations_per_sandbox)
        """
        # Get conversation counts for filtering by max_num_conversations_per_sandbox
        sandbox_conversation_counts = await self._get_conversation_counts_by_sandbox(
            [s.id for s in running_sandboxes]
        )

        # Filter out sandboxes that have reached the max number of conversations
        available_sandboxes = [
            s
            for s in running_sandboxes
            if sandbox_conversation_counts.get(s.id, 0)
            < self.max_num_conversations_per_sandbox
        ]

        if not available_sandboxes:
            # All sandboxes have reached the max - need to create a new one
            return None

        if sandbox_grouping_strategy == SandboxGroupingStrategy.ADD_TO_ANY:
            # Return the first available sandbox
            return available_sandboxes[0]

        elif sandbox_grouping_strategy == SandboxGroupingStrategy.GROUP_BY_NEWEST:
            # Return the most recently created sandbox
            return max(available_sandboxes, key=lambda s: s.created_at)

        elif sandbox_grouping_strategy == SandboxGroupingStrategy.LEAST_RECENTLY_USED:
            # Return the least recently created sandbox (oldest)
            return min(available_sandboxes, key=lambda s: s.created_at)

        elif sandbox_grouping_strategy == SandboxGroupingStrategy.FEWEST_CONVERSATIONS:
            # Return the one with fewest conversations
            return min(
                available_sandboxes,
                key=lambda s: sandbox_conversation_counts.get(s.id, 0),
            )

        else:
            # Default fallback - return first sandbox
            return available_sandboxes[0]