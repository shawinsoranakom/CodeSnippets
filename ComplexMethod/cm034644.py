async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        **kwargs
    ) -> AsyncResult:
        cls.get_models()
        try:
            model = cls.get_model(model)
        except ModelNotFoundError:
            # If get_model fails, use the provided model directly
            model = model

        # Ensure we have an API key before proceeding
        if not cls.api_key:
            raise ProviderException("Failed to obtain API key from authentication endpoint")

        user_prompt = cls.get_last_user_message_content(messages)
        endpoint, signature, timestamp = cls.get_endpoint_signature(cls.api_key,cls.auth_user_id,user_prompt)    
        data = {
            "chat_id": "local",
            "id": str(uuid.uuid4()),
            "stream": True,
            "model": model,
            "messages": messages,
            "params": {},
            "tool_servers": [],
            "features": {
                "enable_thinking": True
            }
        }
        async with StreamSession(
            impersonate="chrome",
            proxy=proxy,
        ) as session:
            async with session.post(
                endpoint,
                json=data,
                headers={
                    "Authorization": f"Bearer {cls.api_key}",
                      "x-fe-version": "prod-fe-1.0.95", 
                      "x-signature": signature
                },
            ) as response:
                await raise_for_status(response)
                usage = None
                async for chunk in response.sse():
                    if chunk.get("type") == "chat:completion":
                        if not usage:
                            usage = chunk.get("data", {}).get("usage")
                            if usage:
                                yield Usage(**usage)
                        if chunk.get("data", {}).get("phase") == "thinking":
                            delta_content = chunk.get("data", {}).get("delta_content")
                            delta_content = delta_content.split("</summary>\n>")[-1] if delta_content else ""
                            if delta_content:
                                yield Reasoning(delta_content)
                        else:
                            edit_content = chunk.get("data", {}).get("edit_content")
                            if edit_content:
                                yield edit_content.split("\n</details>\n")[-1]
                            else:
                                delta_content = chunk.get("data", {}).get("delta_content")
                                if delta_content:
                                    yield delta_content