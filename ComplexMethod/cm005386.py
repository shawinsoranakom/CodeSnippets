async def handle_request(self, body: dict, request_id: str) -> StreamingResponse | JSONResponse:
        """Validate, load model, dispatch to streaming or non-streaming.

        Args:
            body (`dict`): The raw JSON request body (OpenAI Responses API format).
            request_id (`str`): Unique request identifier (from header or auto-generated).

        Returns:
            `StreamingResponse | JSONResponse`: SSE stream or JSON depending on ``body["stream"]``.
        """
        self._validate_request(body)

        model_id, model, processor = self._resolve_model(body)
        modality = self.model_manager.get_model_modality(model, processor=processor)
        use_cb = self.generation_state.use_continuous_batching(model, modality)
        logger.warning(f"[Request received] Model: {model_id}, CB: {use_cb}")
        gen_manager = self.generation_state.get_manager(model_id, use_cb=use_cb)

        # Two-step input conversion (chat completions skips step 1 since messages are already standard):
        # 1. Normalize Responses API input (string/list/dict + instructions) → standard messages list
        # 2. Transform message content for the HF processor (VLM image handling, text joining, etc.)
        messages = self._normalize_input(body)
        processor_inputs = self.get_processor_inputs_from_messages(messages, modality)

        has_video = any(
            c.get("type") == "video"
            for msg in processor_inputs
            for c in (msg.get("content") if isinstance(msg.get("content"), list) else [])
        )

        # Default to 32 frames for video (Gemma 4 default); some processors load all frames otherwise
        chat_template_kwargs = {}
        if has_video:
            chat_template_kwargs["num_frames"] = 32
        # updates the flat tool structure to the one expected by the `apply_chat_template` method.
        tools = self._normalize_tools(body.get("tools"))
        inputs = processor.apply_chat_template(
            processor_inputs,
            add_generation_prompt=True,
            tools=tools,
            return_tensors=None if use_cb else "pt",
            return_dict=True,
            tokenize=True,
            load_audio_from_video=modality == Modality.MULTIMODAL and has_video,
            **chat_template_kwargs,
        )
        if not use_cb:
            inputs = inputs.to(model.device)  # type: ignore[union-attr]

        gen_config = self._build_generation_config(body, model.generation_config, use_cb=use_cb)
        # TODO: remove when CB supports per-request generation config
        if use_cb:
            gen_manager.init_cb(model, gen_config)
        tool_config = get_tool_call_config(processor, model) if body.get("tools") else None

        streaming = body.get("stream", True)
        if streaming:
            return self._streaming(
                request_id,
                model,
                processor,
                model_id,
                body,
                inputs,
                gen_config,
                gen_manager=gen_manager,
                tool_config=tool_config,
            )
        else:
            return await self._non_streaming(
                request_id,
                model,
                processor,
                model_id,
                body,
                inputs,
                gen_config,
                gen_manager=gen_manager,
                tool_config=tool_config,
            )