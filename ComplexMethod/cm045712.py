async def __wrapped__(self, messages: list[dict] | pw.Json, **kwargs) -> str | None:

        messages_decoded = _prepare_messages(messages)

        kwargs = {**self.kwargs, **kwargs}
        kwargs = _extract_value_inside_dict(kwargs)
        verbose = kwargs.pop("verbose", False)

        model_id = kwargs.pop("model_id", None)
        if model_id is None:
            raise ValueError(
                "`model_id` parameter is missing in `BedrockChat`. "
                "Please provide the model ID either in the constructor or in the function call."
            )

        msg_id = str(uuid.uuid4())[-8:]

        event = {
            "_type": "bedrock_chat_request",
            "model_id": model_id,
            "id": msg_id,
            "messages": _prep_message_log(messages_decoded, verbose),
        }
        logger.info(json.dumps(event, ensure_ascii=False))

        # Convert messages to Bedrock format
        bedrock_messages = self._convert_messages_to_bedrock_format(messages_decoded)
        system_prompts = self._extract_system_prompt(messages_decoded)

        # Build inference configuration
        inference_config = {}
        if "max_tokens" in kwargs:
            inference_config["maxTokens"] = kwargs.pop("max_tokens")
        else:
            inference_config["maxTokens"] = 1024  # Default

        if "temperature" in kwargs:
            inference_config["temperature"] = kwargs.pop("temperature")
        if "top_p" in kwargs:
            inference_config["topP"] = kwargs.pop("top_p")
        if "stop_sequences" in kwargs:
            inference_config["stopSequences"] = kwargs.pop("stop_sequences")

        async with self._session.client("bedrock-runtime") as client:
            converse_kwargs = {
                "modelId": model_id,
                "messages": bedrock_messages,
                "inferenceConfig": inference_config,
            }

            if system_prompts:
                converse_kwargs["system"] = system_prompts

            response = await client.converse(**converse_kwargs)

        # Extract response content
        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])

        response_text = None
        for block in content_blocks:
            if "text" in block:
                response_text = block["text"]
                break

        if response_text is not None:
            event = {
                "_type": "bedrock_chat_response",
                "response": (
                    response_text
                    if verbose
                    else response_text[: min(50, len(response_text))] + "..."
                ),
                "id": msg_id,
            }
            logger.info(json.dumps(event, ensure_ascii=False))

        return response_text