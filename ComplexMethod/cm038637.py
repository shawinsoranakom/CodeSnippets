async def create_responses(
        self,
        request: ResponsesRequest,
        raw_request: Request | None = None,
    ) -> (
        AsyncGenerator[StreamingResponsesResponse, None]
        | ResponsesResponse
        | ErrorResponse
    ):
        error_check_ret = await self._check_model(request)
        if error_check_ret is not None:
            logger.error("Error with model %s", error_check_ret)
            return error_check_ret
        maybe_validation_error = self._validate_create_responses_input(request)
        if maybe_validation_error is not None:
            return maybe_validation_error

        # If the engine is dead, raise the engine's DEAD_ERROR.
        # This is required for the streaming case, where we return a
        # success status before we actually start generating text :).
        if self.engine_client.errored:
            raise self.engine_client.dead_error

        if request.store and not self.enable_store:
            # Disable the store option.
            # NOTE(woosuk): Although returning an error is possible, we opted
            # to implicitly disable store and process the request anyway, as
            # we assume most users do not intend to actually store the response
            # (i.e., their request's `store=True` just because it's the default
            # value).
            request.store = False

        # Handle the previous response ID.
        prev_response_id = request.previous_response_id
        if prev_response_id is not None:
            async with self.response_store_lock:
                prev_response = self.response_store.get(prev_response_id)
            if prev_response is None:
                return self._make_not_found_error(prev_response_id)
        else:
            prev_response = None

        lora_request = self._maybe_get_adapters(request)
        model_name = self.models.model_name(lora_request)

        if self.use_harmony:
            messages, engine_inputs = self._make_request_with_harmony(
                request, prev_response
            )
        else:
            messages, engine_inputs = await self._make_request(request, prev_response)

        request_metadata = RequestResponseMetadata(request_id=request.request_id)
        if raw_request:
            raw_request.state.request_metadata = request_metadata

        # Schedule the request and get the result generator.
        max_model_len = self.model_config.max_model_len
        generators: list[AsyncGenerator[ConversationContext, None]] = []

        # Only include builtin tools that the request actually asked for.
        # Without this filter, tools registered on the server (e.g. via
        # --tool-server demo) would be available for execution even when
        # the request didn't enable them.
        requested_tool_types = extract_tool_types(request.tools)
        builtin_tool_list: list[str] = []
        if self.tool_server is not None:
            if (
                self.tool_server.has_tool("browser")
                and "web_search_preview" in requested_tool_types
            ):
                builtin_tool_list.append("browser")
            if (
                self.tool_server.has_tool("python")
                and "code_interpreter" in requested_tool_types
            ):
                builtin_tool_list.append("python")
            if (
                self.tool_server.has_tool("container")
                and "container" in requested_tool_types
            ):
                builtin_tool_list.append("container")

        if self.tool_server is not None:
            available_tools = builtin_tool_list
        else:
            assert len(builtin_tool_list) == 0
            available_tools = []
        tokenizer = self.renderer.get_tokenizer()

        for engine_input in engine_inputs:
            maybe_error = self._validate_generator_input(engine_input)
            if maybe_error is not None:
                return maybe_error

            default_max_tokens = get_max_tokens(
                max_model_len,
                request.max_output_tokens,
                self._extract_prompt_len(engine_input),
                self.default_sampling_params,
                self.override_max_tokens,
            )

            sampling_params = request.to_sampling_params(
                default_max_tokens, self.default_sampling_params
            )

            trace_headers = (
                None
                if raw_request is None
                else await self._get_trace_headers(raw_request.headers)
            )

            context: ConversationContext
            if self.use_harmony:
                if request.stream:
                    context = StreamingHarmonyContext(messages, available_tools)
                else:
                    context = HarmonyContext(messages, available_tools)
            else:
                if envs.VLLM_USE_EXPERIMENTAL_PARSER_CONTEXT:
                    # This is a feature in development for parsing
                    # tokens during generation instead of at the end
                    context = ParsableContext(
                        response_messages=messages,
                        tokenizer=tokenizer,
                        reasoning_parser_cls=self.parser.reasoning_parser_cls
                        if self.parser
                        else None,
                        request=request,
                        tool_parser_cls=self.parser.tool_parser_cls
                        if self.parser
                        else None,
                        available_tools=available_tools,
                        chat_template=self.chat_template,
                        chat_template_content_format=self.chat_template_content_format,
                    )
                else:
                    context = SimpleContext()

            if self.parser and self.parser.reasoning_parser_cls is not None:
                reasoning_parser = self.parser.reasoning_parser_cls(
                    tokenizer,
                    chat_template_kwargs=self._effective_chat_template_kwargs(request),
                )
                if (
                    isinstance(
                        struct_out := sampling_params.structured_outputs,
                        StructuredOutputsParams,
                    )
                    and struct_out.all_non_structural_tag_constraints_none()
                ):
                    sampling_params.structured_outputs = replace(
                        struct_out,
                        structural_tag=reasoning_parser.prepare_structured_tag(
                            struct_out.structural_tag, self.tool_server
                        ),
                    )
            generator = self._generate_with_builtin_tools(
                request_id=request.request_id,
                engine_input=engine_input,
                sampling_params=sampling_params,
                context=context,
                lora_request=lora_request,
                priority=request.priority,
                trace_headers=trace_headers,
            )
            generators.append(generator)

        assert len(generators) == 1
        (result_generator,) = generators

        # Store the input messages.
        if request.store:
            self.msg_store[request.request_id] = messages

        if request.background:
            created_time = int(time.time())
            response = ResponsesResponse.from_request(
                request,
                sampling_params,
                model_name=model_name,
                created_time=created_time,
                output=[],
                status="queued",
                usage=None,
            )
            async with self.response_store_lock:
                self.response_store[response.id] = response

            # Run the request in the background.
            if request.stream:
                task = asyncio.create_task(
                    self._run_background_request_stream(
                        request,
                        sampling_params,
                        result_generator,
                        context,
                        model_name,
                        tokenizer,
                        request_metadata,
                        created_time,
                    ),
                    name=f"create_{request.request_id}",
                )
            else:
                task = asyncio.create_task(
                    self._run_background_request(
                        request,
                        sampling_params,
                        result_generator,
                        context,
                        model_name,
                        tokenizer,
                        request_metadata,
                        created_time,
                    ),
                    name=f"create_{response.id}",
                )

            # For cleanup.
            response_id = response.id
            self.background_tasks[response_id] = task
            task.add_done_callback(
                lambda _: self.background_tasks.pop(response_id, None)
            )

            if request.stream:
                return self.responses_background_stream_generator(request.request_id)
            return response

        if request.stream:
            return self.responses_stream_generator(
                request,
                sampling_params,
                result_generator,
                context,
                model_name,
                tokenizer,
                request_metadata,
            )

        return await self.responses_full_generator(
            request,
            sampling_params,
            result_generator,
            context,
            model_name,
            tokenizer,
            request_metadata,
        )