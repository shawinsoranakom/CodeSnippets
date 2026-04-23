def get_messages(self) -> Iterator[ChatMessage]:
        messages: list[ChatMessage] = []
        step_summaries: list[str] = []
        tokens: int = 0
        n_episodes = len(self.event_history.episodes)

        # Include a summary for all except a few latest steps
        for i, episode in enumerate(reversed(self.event_history.episodes)):
            # Use full format for a few steps, summary or format for older steps
            if i < self.config.full_message_count:
                messages.insert(0, episode.action.raw_message)
                tokens += self.count_tokens(str(messages[0]))  # HACK
                if episode.result:
                    # Create result messages for ALL tool calls
                    # (required by Anthropic API)
                    result_messages = self._make_result_messages(
                        episode, episode.result
                    )
                    # Insert in reverse order so they appear in correct order
                    for j, result_message in enumerate(result_messages):
                        messages.insert(1 + j, result_message)
                        tokens += self.count_tokens(str(result_message))  # HACK
                continue
            elif episode.summary is None:
                step_content = indent(episode.format(), 2).strip()
            else:
                step_content = episode.summary

            step = f"* Step {n_episodes - i}: {step_content}"

            if self.config.max_tokens and self.count_tokens:
                step_tokens = self.count_tokens(step)
                if tokens + step_tokens > self.config.max_tokens:
                    break
                tokens += step_tokens

            step_summaries.insert(0, step)

        if step_summaries:
            step_summaries_fmt = "\n\n".join(step_summaries)
            yield ChatMessage.user(
                f"## Progress on your Task so far\n"
                "Here is a summary of the steps that you have executed so far, "
                "use this as your consideration for determining the next action!\n"
                f"{step_summaries_fmt}"
            )

        yield from messages

        # Include any pending user feedback as a prominent user message.
        # This ensures the agent pays attention to what the user said,
        # whether they approved a command with feedback or denied it.
        pending_feedback = self.event_history.pop_pending_feedback()
        if pending_feedback:
            feedback_text = "\n".join(f"- {feedback}" for feedback in pending_feedback)
            yield ChatMessage.user(
                f"[USER FEEDBACK] The user provided the following feedback. "
                f"Read it carefully and adjust your approach accordingly:\n"
                f"{feedback_text}"
            )