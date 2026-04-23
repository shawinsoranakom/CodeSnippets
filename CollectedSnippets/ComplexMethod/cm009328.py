async def _aiterate_over_stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        reasoning = kwargs.get("reasoning", self.reasoning)
        async for stream_resp in self._acreate_chat_stream(messages, stop, **kwargs):
            if not isinstance(stream_resp, str):
                content = (
                    stream_resp["message"]["content"]
                    if "message" in stream_resp and "content" in stream_resp["message"]
                    else ""
                )

                # Warn and skip responses with done_reason: 'load' and empty content
                # These indicate the model was loaded but no actual generation occurred
                is_load_response_with_empty_content = (
                    stream_resp.get("done") is True
                    and stream_resp.get("done_reason") == "load"
                    and not content.strip()
                )

                if is_load_response_with_empty_content:
                    log.warning(
                        "Ollama returned empty response with done_reason='load'. "
                        "This typically indicates the model was loaded but no content "
                        "was generated. Skipping this response."
                    )
                    continue

                if stream_resp.get("done") is True:
                    generation_info = dict(stream_resp)
                    if "model" in generation_info:
                        generation_info["model_name"] = generation_info["model"]
                    generation_info["model_provider"] = "ollama"
                    _ = generation_info.pop("message", None)
                else:
                    chunk_logprobs = stream_resp.get("logprobs")
                    generation_info = (
                        {"logprobs": chunk_logprobs}
                        if chunk_logprobs is not None
                        else None
                    )

                additional_kwargs = {}
                if (
                    reasoning
                    and "message" in stream_resp
                    and (thinking_content := stream_resp["message"].get("thinking"))
                ):
                    additional_kwargs["reasoning_content"] = thinking_content

                chunk = ChatGenerationChunk(
                    message=AIMessageChunk(
                        content=content,
                        additional_kwargs=additional_kwargs,
                        usage_metadata=_get_usage_metadata_from_generation_info(
                            stream_resp
                        ),
                        tool_calls=_get_tool_calls_from_response(stream_resp),
                    ),
                    generation_info=generation_info,
                )

                yield chunk