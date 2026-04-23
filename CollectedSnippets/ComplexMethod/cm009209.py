async def _astream(
        self,
        prompt: str,
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        r"""Call Anthropic completion_stream and return the resulting generator.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.
            run_manager: Optional callback manager for LLM run.
            kwargs: Additional keyword arguments to pass to the model.

        Returns:
            A generator representing the stream of tokens from Anthropic.

        Example:
            ```python
            prompt = "Write a poem about a stream."
            prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
            generator = anthropic.stream(prompt)
            for token in generator:
                yield token
            ```
        """
        stop = self._get_anthropic_stop(stop)
        params = {**self._default_params, **kwargs}

        # Remove parameters not supported by Messages API
        params = {k: v for k, v in params.items() if k != "max_tokens_to_sample"}

        async with self.async_client.messages.stream(
            messages=self._format_messages(prompt),
            stop_sequences=stop if stop else None,
            **params,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                    chunk = GenerationChunk(text=event.delta.text)
                    if run_manager:
                        await run_manager.on_llm_new_token(chunk.text, chunk=chunk)
                    yield chunk