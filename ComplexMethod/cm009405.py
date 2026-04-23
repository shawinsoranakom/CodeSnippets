async def _astream(
        self,
        prompt: str,
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        invocation_params = self._invocation_params(stop, **kwargs)
        async for response in await self.async_client.text_generation(
            prompt, **invocation_params, stream=True
        ):
            # identify stop sequence in generated text, if any
            stop_seq_found: str | None = None
            for stop_seq in invocation_params["stop"]:
                if stop_seq in response:
                    stop_seq_found = stop_seq

            # identify text to yield
            text: str | None = None
            if stop_seq_found:
                text = response[: response.index(stop_seq_found)]
            else:
                text = response

            # yield text, if any
            if text:
                chunk = GenerationChunk(text=text)

                if run_manager:
                    await run_manager.on_llm_new_token(chunk.text)
                yield chunk

            # break if stop sequence found
            if stop_seq_found:
                break