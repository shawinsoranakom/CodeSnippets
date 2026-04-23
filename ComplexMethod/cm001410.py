def _compile_progress(
        self,
        episode_history: list[Episode[AnyProposal]],
        max_tokens: Optional[int] = None,
        count_tokens: Optional[Callable[[str], int]] = None,
    ) -> str:
        if max_tokens and not count_tokens:
            raise ValueError("count_tokens is required if max_tokens is set")

        steps: list[str] = []
        tokens: int = 0
        n_episodes = len(episode_history)

        for i, episode in enumerate(reversed(episode_history)):
            # Use full format for a few latest steps, summary or format for older steps
            if i < self.config.full_message_count or episode.summary is None:
                step_content = indent(episode.format(), 2).strip()
            else:
                step_content = episode.summary

            step = f"* Step {n_episodes - i}: {step_content}"

            if max_tokens and count_tokens:
                step_tokens = count_tokens(step)
                if tokens + step_tokens > max_tokens:
                    break
                tokens += step_tokens

            steps.insert(0, step)

        return "\n\n".join(steps)