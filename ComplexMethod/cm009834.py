def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream the output of the model."""
        chat_result = self._generate(
            messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )
        if not isinstance(chat_result, ChatResult):
            msg = (  # type: ignore[unreachable]
                f"Expected generate to return a ChatResult, "
                f"but got {type(chat_result)} instead."
            )
            raise TypeError(msg)

        message = chat_result.generations[0].message

        if not isinstance(message, AIMessage):
            msg = (
                f"Expected invoke to return an AIMessage, "
                f"but got {type(message)} instead."
            )
            raise TypeError(msg)

        content = message.content

        if content:
            # Use a regular expression to split on whitespace with a capture group
            # so that we can preserve the whitespace in the output.
            assert isinstance(content, str)
            content_chunks = cast("list[str]", re.split(r"(\s)", content))

            for idx, token in enumerate(content_chunks):
                chunk = ChatGenerationChunk(
                    message=AIMessageChunk(id=message.id, content=token),
                )
                if (
                    idx == len(content_chunks) - 1
                    and isinstance(chunk.message, AIMessageChunk)
                    and not message.additional_kwargs
                ):
                    chunk.message.chunk_position = "last"
                if run_manager:
                    run_manager.on_llm_new_token(token, chunk=chunk)
                yield chunk

        if message.additional_kwargs:
            for key, value in message.additional_kwargs.items():
                # We should further break down the additional kwargs into chunks
                # Special case for function call
                if key == "function_call":
                    for fkey, fvalue in value.items():
                        if isinstance(fvalue, str):
                            # Break function call by `,`
                            fvalue_chunks = cast("list[str]", re.split(r"(,)", fvalue))
                            for fvalue_chunk in fvalue_chunks:
                                chunk = ChatGenerationChunk(
                                    message=AIMessageChunk(
                                        id=message.id,
                                        content="",
                                        additional_kwargs={
                                            "function_call": {fkey: fvalue_chunk},
                                        },
                                    ),
                                )
                                if run_manager:
                                    run_manager.on_llm_new_token(
                                        "",
                                        chunk=chunk,  # No token for function call
                                    )
                                yield chunk
                        else:
                            chunk = ChatGenerationChunk(
                                message=AIMessageChunk(
                                    id=message.id,
                                    content="",
                                    additional_kwargs={"function_call": {fkey: fvalue}},
                                ),
                            )
                            if run_manager:
                                run_manager.on_llm_new_token(
                                    "",
                                    chunk=chunk,  # No token for function call
                                )
                            yield chunk
                else:
                    chunk = ChatGenerationChunk(
                        message=AIMessageChunk(
                            id=message.id,
                            content="",
                            additional_kwargs={key: value},
                        ),
                    )
                    if run_manager:
                        run_manager.on_llm_new_token(
                            "",
                            chunk=chunk,  # No token for function call
                        )
                    yield chunk