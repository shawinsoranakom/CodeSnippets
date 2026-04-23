async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        stream = await self.aclient.messages.create(**self._const_kwargs(messages, stream=True))
        collected_content = []
        collected_reasoning_content = []
        usage = Usage(input_tokens=0, output_tokens=0)
        async for event in stream:
            event_type = event.type
            if event_type == "message_start":
                usage.input_tokens = event.message.usage.input_tokens
                usage.output_tokens = event.message.usage.output_tokens
            elif event_type == "content_block_delta":
                delta_type = event.delta.type
                if delta_type == "thinking_delta":
                    collected_reasoning_content.append(event.delta.thinking)
                elif delta_type == "text_delta":
                    content = event.delta.text
                    log_llm_stream(content)
                    collected_content.append(content)
            elif event_type == "message_delta":
                usage.output_tokens = event.usage.output_tokens  # update final output_tokens

        log_llm_stream("\n")
        self._update_costs(usage)
        full_content = "".join(collected_content)
        if collected_reasoning_content:
            self.reasoning_content = "".join(collected_reasoning_content)
        return full_content