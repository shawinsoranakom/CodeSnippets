def reset_matching(
        self,
        strategy: str | None = None,
        model: str | None = None,
        challenge: str | None = None,
    ) -> int:
        """Reset runs matching the given criteria.

        Args:
            strategy: Reset runs with this strategy (e.g., "reflexion").
            model: Reset runs with this model (e.g., "claude-thinking-25k").
            challenge: Reset runs for this challenge name.

        Returns:
            Number of runs reset.
        """
        state = self.load()
        keys_to_remove = []

        for key, run in state.completed_runs.items():
            # Parse config_name which is "{strategy}/{model}"
            parts = run.config_name.split("/")
            run_strategy = parts[0] if len(parts) > 0 else ""
            run_model = parts[1] if len(parts) > 1 else ""

            # Check if this run matches the criteria
            matches = True
            if strategy and run_strategy != strategy:
                matches = False
            if model and run_model != model:
                matches = False
            if challenge and run.challenge_name != challenge:
                matches = False

            if matches:
                keys_to_remove.append(key)

        # Remove matching runs
        for key in keys_to_remove:
            del state.completed_runs[key]

        if keys_to_remove:
            self.save()

        return len(keys_to_remove)