def stream(
        self,
        input: LanguageModelInput,
        config: RunnableConfig | None = None,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> Iterator[AIMessageChunk]:
        if not self._should_stream(async_api=False, **{**kwargs, "stream": True}):
            # Model doesn't implement streaming, so use default implementation
            yield cast(
                "AIMessageChunk",
                self.invoke(input, config=config, stop=stop, **kwargs),
            )
        else:
            config = ensure_config(config)
            messages = self._convert_input(input).to_messages()
            ls_structured_output_format = kwargs.pop(
                "ls_structured_output_format", None
            ) or kwargs.pop("structured_output_format", None)
            ls_structured_output_format_dict = _format_ls_structured_output(
                ls_structured_output_format
            )

            params = self._get_invocation_params(stop=stop, **kwargs)
            options = {"stop": stop, **kwargs, **ls_structured_output_format_dict}
            inheritable_metadata = {
                **(config.get("metadata") or {}),
                **self._get_ls_params_with_defaults(stop=stop, **kwargs),
            }
            callback_manager = CallbackManager.configure(
                config.get("callbacks"),
                self.callbacks,
                self.verbose,
                config.get("tags"),
                self.tags,
                inheritable_metadata,
                self.metadata,
                langsmith_inheritable_metadata=_filter_invocation_params_for_tracing(
                    params
                ),
            )
            (run_manager,) = callback_manager.on_chat_model_start(
                self._serialized,
                [_format_for_tracing(messages)],
                invocation_params=params,
                options=options,
                name=config.get("run_name"),
                run_id=config.pop("run_id", None),
                batch_size=1,
            )

            chunks: list[ChatGenerationChunk] = []

            if self.rate_limiter:
                self.rate_limiter.acquire(blocking=True)

            try:
                input_messages = _normalize_messages(messages)
                run_id = "-".join((LC_ID_PREFIX, str(run_manager.run_id)))
                yielded = False
                index = -1
                index_type = ""
                for chunk in self._stream(input_messages, stop=stop, **kwargs):
                    if chunk.message.id is None:
                        chunk.message.id = run_id
                    chunk.message.response_metadata = _gen_info_and_msg_metadata(chunk)
                    if self.output_version == "v1":
                        # Overwrite .content with .content_blocks
                        chunk.message = _update_message_content_to_blocks(
                            chunk.message, "v1"
                        )
                        for block in cast(
                            "list[types.ContentBlock]", chunk.message.content
                        ):
                            if block["type"] != index_type:
                                index_type = block["type"]
                                index += 1
                            if "index" not in block:
                                block["index"] = index
                    run_manager.on_llm_new_token(
                        cast("str", chunk.message.content), chunk=chunk
                    )
                    chunks.append(chunk)
                    yield cast("AIMessageChunk", chunk.message)
                    yielded = True

                # Yield a final empty chunk with chunk_position="last" if not yet
                # yielded
                if (
                    yielded
                    and isinstance(chunk.message, AIMessageChunk)
                    and not chunk.message.chunk_position
                ):
                    empty_content: str | list = (
                        "" if isinstance(chunk.message.content, str) else []
                    )
                    msg_chunk = AIMessageChunk(
                        content=empty_content, chunk_position="last", id=run_id
                    )
                    run_manager.on_llm_new_token(
                        "", chunk=ChatGenerationChunk(message=msg_chunk)
                    )
                    yield msg_chunk
            except BaseException as e:
                generations_with_error_metadata = _generate_response_from_error(e)
                chat_generation_chunk = merge_chat_generation_chunks(chunks)
                if chat_generation_chunk:
                    generations = [
                        [chat_generation_chunk],
                        generations_with_error_metadata,
                    ]
                else:
                    generations = [generations_with_error_metadata]
                run_manager.on_llm_error(
                    e,
                    response=LLMResult(generations=generations),
                )
                raise

            generation = merge_chat_generation_chunks(chunks)
            if generation is None:
                err = ValueError("No generation chunks were returned")
                run_manager.on_llm_error(err, response=LLMResult(generations=[]))
                raise err

            run_manager.on_llm_end(LLMResult(generations=[[generation]]))