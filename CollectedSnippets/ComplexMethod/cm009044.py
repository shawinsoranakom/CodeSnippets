def _should_summarize_based_on_reported_tokens(
        self, messages: list[AnyMessage], threshold: float
    ) -> bool:
        """Check if reported token usage from last AIMessage exceeds threshold."""
        last_ai_message = next(
            (msg for msg in reversed(messages) if isinstance(msg, AIMessage)),
            None,
        )
        if (  # noqa: SIM103
            isinstance(last_ai_message, AIMessage)
            and last_ai_message.usage_metadata is not None
            and (reported_tokens := last_ai_message.usage_metadata.get("total_tokens", -1))
            and reported_tokens >= threshold
            and (message_provider := last_ai_message.response_metadata.get("model_provider"))
            and message_provider == self.model._get_ls_params().get("ls_provider")  # noqa: SLF001
        ):
            return True
        return False