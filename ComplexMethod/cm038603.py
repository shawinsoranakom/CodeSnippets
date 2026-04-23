async def chat_completion_full_generator_batch(
        self,
        request: BatchChatCompletionRequest,  # type: ignore[override]
        generators: list[AsyncGenerator[RequestOutput, None]],
        request_id: str,
        model_name: str,
        all_conversations: list[list[ConversationMessage]],
        tokenizer: TokenizerLike,
        request_metadata: RequestResponseMetadata,
        reasoning_parser: ReasoningParser | None = None,
    ) -> ErrorResponse | ChatCompletionResponse:
        """Handle batched (non-streaming) chat completions.

        Fans out N generators (one per conversation in the batch), collects
        the final output for each, and assembles a single
        ``ChatCompletionResponse`` whose ``choices`` are indexed 0,...,N-1.

        Tool-use and streaming are rejected upstream by the
        ``check_batch_mode`` validator, so neither needs to be handled here.
        """
        created_time = int(time.time())
        role = self.get_chat_request_role(request)  # type: ignore[arg-type]

        final_results: dict[int, RequestOutput] = {}
        try:
            async for prompt_idx, res in merge_async_iterators(*generators):
                final_results[prompt_idx] = res
        except asyncio.CancelledError:
            return self.create_error_response("Client disconnected")

        choices: list[ChatCompletionResponseChoice] = []
        total_prompt_tokens = 0
        total_completion_tokens = 0

        for prompt_idx in range(len(generators)):
            final_res = final_results.get(prompt_idx)
            if final_res is None:
                return self.create_error_response(
                    f"No output received from the engine for prompt {prompt_idx}.",
                    err_type="InternalServerError",
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            assert final_res.prompt_token_ids is not None
            num_prompt_tokens = len(final_res.prompt_token_ids)
            if final_res.encoder_prompt_token_ids is not None:
                num_prompt_tokens += len(final_res.encoder_prompt_token_ids)
            total_prompt_tokens += num_prompt_tokens
            total_completion_tokens += sum(
                len(output.token_ids) for output in final_res.outputs
            )

            for output in final_res.outputs:
                self._raise_if_error(output.finish_reason, request_id)

                if request.logprobs and request.top_logprobs is not None:
                    assert output.logprobs is not None, "Did not output logprobs"
                    logprobs = self._create_chat_logprobs(
                        token_ids=output.token_ids,
                        top_logprobs=output.logprobs,
                        num_output_top_logprobs=request.top_logprobs,
                        tokenizer=tokenizer,
                        return_as_token_id=request.return_token_ids,
                    )
                else:
                    logprobs = None

                if reasoning_parser:
                    reasoning, content = reasoning_parser.extract_reasoning(
                        output.text,
                        request=request,  # type: ignore[arg-type]
                    )
                    if not getattr(request, "include_reasoning", True):
                        reasoning = None
                else:
                    reasoning = None
                    content = output.text

                message = ChatMessage(role=role, reasoning=reasoning, content=content)

                if request.echo:
                    conversation = all_conversations[prompt_idx]
                    last_msg_content: str | list[dict[str, str]] = ""
                    if conversation and "content" in conversation[-1]:
                        last_msg_content = conversation[-1]["content"] or ""
                    if isinstance(last_msg_content, list):
                        last_msg_content = "\n".join(
                            msg["text"] for msg in last_msg_content
                        )
                    message.content = last_msg_content + (message.content or "")

                choice_data = ChatCompletionResponseChoice(
                    index=prompt_idx,
                    message=message,
                    logprobs=logprobs,
                    finish_reason=output.finish_reason
                    if output.finish_reason
                    else "stop",
                    stop_reason=output.stop_reason,
                    token_ids=(
                        as_list(output.token_ids) if request.return_token_ids else None
                    ),
                )
                choices.append(choice_data)

        usage = UsageInfo(
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            total_tokens=total_prompt_tokens + total_completion_tokens,
        )
        request_metadata.final_usage_info = usage

        choices.sort(key=lambda c: c.index)

        return ChatCompletionResponse(
            id=request_id,
            created=created_time,
            model=model_name,
            choices=choices,
            usage=usage,
        )