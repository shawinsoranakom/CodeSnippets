async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        api_key: str = None,
        base_url: str = None,
        **kwargs
    ) -> AsyncResult:
        try:
            creds = await cls.client.get_valid_token()
            last_chunk = None
            async for chunk in super().create_async_generator(
                model,
                messages,
                api_key=creds.get("token", api_key),
                base_url=creds.get("endpoint", base_url),
                **kwargs
            ):
                if isinstance(chunk, str):
                    if chunk != last_chunk:
                        yield chunk
                    last_chunk = chunk
                else:
                    yield chunk
        except TokenManagerError:
            await cls.client.shared_manager.getValidCredentials(cls.client.qwen_client, True)
            creds = await cls.client.get_valid_token()
            last_chunk = None
            async for chunk in super().create_async_generator(
                model,
                messages,
                api_key=creds.get("token"),
                base_url=creds.get("endpoint"),
                **kwargs
            ):
                if isinstance(chunk, str):
                    if chunk != last_chunk:
                        yield chunk
                    last_chunk = chunk
                else:
                    yield chunk
        except Exception:
            raise