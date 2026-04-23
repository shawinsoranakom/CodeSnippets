def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Collect token usage."""
        # Check for usage_metadata (langchain-core >= 0.2.2)
        try:
            generation = response.generations[0][0]
        except IndexError:
            generation = None

        usage_metadata = None
        model_name = None
        if isinstance(generation, ChatGeneration):
            try:
                message = generation.message
                if isinstance(message, AIMessage):
                    usage_metadata = message.usage_metadata
                    model_name = message.response_metadata.get("model_name")
            except AttributeError:
                pass

        # update shared state behind lock
        if usage_metadata and model_name:
            with self._lock:
                if model_name not in self.usage_metadata:
                    self.usage_metadata[model_name] = usage_metadata
                else:
                    self.usage_metadata[model_name] = add_usage(
                        self.usage_metadata[model_name], usage_metadata
                    )