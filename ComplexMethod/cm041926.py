async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
        response: AsyncStream[ChatCompletionChunk] = await self.aclient.chat.completions.create(
            **self._cons_kwargs(messages, timeout=self.get_timeout(timeout)), stream=True
        )
        usage = None
        collected_messages = []
        collected_reasoning_messages = []
        has_finished = False
        async for chunk in response:
            if not chunk.choices:
                continue

            choice0 = chunk.choices[0]
            choice_delta = choice0.delta
            if hasattr(choice_delta, "reasoning_content") and choice_delta.reasoning_content:
                collected_reasoning_messages.append(choice_delta.reasoning_content)  # for deepseek
                continue
            chunk_message = choice_delta.content or ""  # extract the message
            finish_reason = choice0.finish_reason if hasattr(choice0, "finish_reason") else None
            log_llm_stream(chunk_message)
            collected_messages.append(chunk_message)
            chunk_has_usage = hasattr(chunk, "usage") and chunk.usage
            if has_finished:
                # for oneapi, there has a usage chunk after finish_reason not none chunk
                if chunk_has_usage:
                    usage = CompletionUsage(**chunk.usage) if isinstance(chunk.usage, dict) else chunk.usage
            if finish_reason:
                if chunk_has_usage:
                    # Some services have usage as an attribute of the chunk, such as Fireworks
                    usage = CompletionUsage(**chunk.usage) if isinstance(chunk.usage, dict) else chunk.usage
                elif hasattr(choice0, "usage"):
                    # The usage of some services is an attribute of chunk.choices[0], such as Moonshot
                    usage = CompletionUsage(**choice0.usage)
                has_finished = True

        log_llm_stream("\n")
        full_reply_content = "".join(collected_messages)
        if collected_reasoning_messages:
            self.reasoning_content = "".join(collected_reasoning_messages)
        if not usage:
            # Some services do not provide the usage attribute, such as OpenAI or OpenLLM
            usage = self._calc_usage(messages, full_reply_content)

        self._update_costs(usage)
        return full_reply_content