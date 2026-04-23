async def create_authed(
        cls,
        model: str,
        messages: Messages,
        auth_result: AuthResult,
        conversation: Conversation = None,
        **kwargs
    ) -> AsyncResult:
        conversation_id = None if conversation is None else conversation.conversation_id
        prompt = format_prompt(messages) if conversation_id is None else get_last_user_message(messages)

        async with StreamSession(
            **auth_result.get_dict()
        ) as session:
            payload = await cls._prepare_payload(model, prompt)

            # Add voice mode support flag (for future use)
            if kwargs.get("enable_voice", False):
                payload["enableVoiceMode"] = True

            if conversation_id is None:
                url = f"{cls.conversation_url}/new"
            else:
                url = f"{cls.conversation_url}/{conversation_id}/responses"

            async with session.post(url, json=payload, headers={"x-xai-request-id": str(uuid.uuid4())}) as response:
                if response.status == 403:
                    raise MissingAuthError("Invalid secrets")
                auth_result.cookies = merge_cookies(auth_result.cookies, response)
                await raise_for_status(response)

                thinking_duration = None
                deep_search_active = False

                async for line in response.iter_lines():
                    if line:
                        try:
                            json_data = json.loads(line)
                            result = json_data.get("result", {})

                            if conversation_id is None:
                                conversation_id = result.get("conversation", {}).get("conversationId")

                            response_data = result.get("response", {})

                            # Handle DeepSearch status
                            deep_search = response_data.get("deepSearchStatus")
                            if deep_search:
                                if not deep_search_active:
                                    deep_search_active = True
                                    yield Reasoning(status="🔍 Deep searching...")
                                if deep_search.get("completed"):
                                    deep_search_active = False
                                    yield Reasoning(status="Deep search completed")

                            # Handle image generation (Aurora for Grok 3+)
                            image = response_data.get("streamingImageGenerationResponse", None)
                            if image is not None:
                                image_url = image.get("imageUrl")
                                if image_url:
                                    yield ImagePreview(
                                        f'{cls.assets_url}/{image_url}',
                                        "",
                                        {"cookies": auth_result.cookies, "headers": auth_result.headers}
                                    )

                            # Handle text tokens
                            token = response_data.get("token", result.get("token"))
                            is_thinking = response_data.get("isThinking", result.get("isThinking"))

                            if token:
                                if is_thinking:
                                    if thinking_duration is None:
                                        thinking_duration = time.time()
                                        # Different status for different models
                                        if "grok-4" in model:
                                            status = "🧠 Grok 4 is processing..."
                                        elif "big-brain" in payload and payload["enableBigBrain"]:
                                            status = "🧠 Big Brain mode active..."
                                        else:
                                            status = "🤔 Is thinking..."
                                        yield Reasoning(status=status)
                                    yield Reasoning(token)
                                else:
                                    if thinking_duration is not None:
                                        thinking_duration = time.time() - thinking_duration
                                        status = f"Thought for {thinking_duration:.2f}s" if thinking_duration > 1 else ""
                                        thinking_duration = None
                                        yield Reasoning(status=status)
                                    yield token

                            # Handle generated images
                            generated_images = response_data.get("modelResponse", {}).get("generatedImageUrls", None)
                            if generated_images:
                                yield ImageResponse(
                                    [f'{cls.assets_url}/{image}' for image in generated_images],
                                    "",
                                    {"cookies": auth_result.cookies, "headers": auth_result.headers}
                                )

                            # Handle title generation
                            title = result.get("title", {}).get("newTitle", "")
                            if title:
                                yield TitleGeneration(title)

                            # Handle tool usage information (Grok 4)
                            tool_usage = response_data.get("toolUsage")
                            if tool_usage:
                                tools_used = tool_usage.get("toolsUsed", [])
                                if tools_used:
                                    yield Reasoning(status=f"Used tools: {', '.join(tools_used)}")

                        except json.JSONDecodeError:
                            continue

                # Return conversation ID for continuation
                if conversation_id is not None and kwargs.get("return_conversation", False):
                    yield Conversation(conversation_id)