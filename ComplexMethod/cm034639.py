async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncResult:
        cache_file = cls.get_cache_file()
        if cls._args is None:
            headers = DEFAULT_HEADERS.copy()
            headers["referer"] = f"{cls.url}"
            headers["origin"] = cls.url
            if cache_file.exists():
                with cache_file.open("r") as f:
                    cls._args = json.load(f)
            elif has_nodriver:
                try:
                    cls._args = await get_args_from_nodriver(cls.url, proxy=proxy)
                except (RuntimeError, FileNotFoundError) as e:
                    debug.log(f"Cloudflare: Nodriver is not available:", e)
                    cls._args = {"headers": headers, "cookies": {}, "impersonate": "chrome"}
            else:
                cls._args = {"headers": headers, "cookies": {}, "impersonate": "chrome"}
        try:
            model = cls.get_model(model)
        except ModelNotFoundError:
            pass
        data = {
            "messages": [{
                **message,
                "parts": [{"type":"text", "text": message["content"]}]} for message in render_messages(messages)],
            "lora": None,
            "model": model,
            "max_tokens": max_tokens,
            "stream": True,
            "system_message":"You are a helpful assistant",
            "tools":[]
        }
        async with StreamSession(**cls._args) as session:
            async with session.post(
                cls.api_endpoint,
                json=data,
            ) as response:
                cls._args["cookies"] = merge_cookies(cls._args["cookies"] , response)
                try:
                    await raise_for_status(response)
                except ResponseStatusError:
                    cls._args = None
                    if cache_file.exists():
                        cache_file.unlink()
                    raise
                async for line in response.iter_lines():
                    if line.startswith(b'0:'):
                        yield json.loads(line[2:])
                    elif line.startswith(b'e:'):
                        finish = json.loads(line[2:])
                        yield Usage(**finish.get("usage"))
                        yield FinishReason(finish.get("finishReason"))
        with cache_file.open("w") as f:
            json.dump(cls._args, f)