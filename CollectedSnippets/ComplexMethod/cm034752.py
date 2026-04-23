async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        stream: bool = True,
        proxy: str = None,
        timeout: int = 600,
        base_url: str = "https://api-inference.huggingface.co",
        api_key: str = None,
        max_tokens: int = 1024,
        temperature: float = None,
        prompt: str = None,
        action: str = None,
        extra_body: dict = None,
        seed: int = None,
        aspect_ratio: str = None,
        width: int = None,
        height: int = None,
        **kwargs
    ) -> AsyncResult:
        try:
            model = cls.get_model(model)
        except ModelNotFoundError:
            pass
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/json',
        }
        if api_key is not None:
            headers["Authorization"] = f"Bearer {api_key}"
        if extra_body is None:
            extra_body = {}
        image_extra_body = use_aspect_ratio({
            "width": width,
            "height": height,
            **extra_body
        }, aspect_ratio)
        async with StreamSession(
            headers=headers,
            proxy=proxy,
            timeout=timeout
        ) as session:
            try:
                if model in provider_together_urls:
                    data = {
                        "response_format": "url",
                        "prompt": format_media_prompt(messages, prompt),
                        "model": model,
                        **image_extra_body
                    }
                    async with session.post(provider_together_urls[model], json=data) as response:
                        if response.status == 404:
                            raise ModelNotFoundError(f"Model not found: {model}")
                        await raise_for_status(response)
                        result = await response.json()
                        yield ImageResponse([item["url"] for item in result["data"]], data["prompt"])
                    return
            except ModelNotFoundError:
                pass
            payload = None
            params = {
                "return_full_text": False,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                **extra_body
            }
            do_continue = action == "continue"
            if payload is None:
                model_data = await cls.get_model_data(session, model)
                pipeline_tag = model_data.get("pipeline_tag")
                if pipeline_tag == "text-to-image":
                    stream = False
                    inputs = format_media_prompt(messages, prompt)
                    payload = {"inputs": inputs, "parameters": {"seed": random.randint(0, 2**32) if seed is None else seed, **image_extra_body}}
                elif pipeline_tag in ("text-generation", "image-text-to-text"):
                    model_type = None
                    if "config" in model_data and "model_type" in model_data["config"]:
                        model_type = model_data["config"]["model_type"]
                    debug.log(f"Model type: {model_type}")
                    inputs = get_inputs(messages, model_data, model_type, do_continue)
                    debug.log(f"Inputs len: {len(inputs)}")
                    if len(inputs) > 4096:
                        if len(messages) > 6:
                            messages = messages[:3] + messages[-3:]
                        else:
                            messages = [m for m in messages if m["role"] == "system"] + [{"role": "user", "content": get_last_user_message(messages)}]
                        inputs = get_inputs(messages, model_data, model_type, do_continue)
                        debug.log(f"New len: {len(inputs)}")
                    if model_type == "gpt2" and max_tokens >= 1024:
                        params["max_new_tokens"] = 512
                    if seed is not None:
                        params["seed"] = seed
                    payload = {"inputs": inputs, "parameters": params, "stream": stream}
                else:
                    raise ModelNotFoundError(f"Model is not supported: {model} in: {cls.__name__} pipeline_tag: {pipeline_tag}")

            async with session.post(f"{base_url.rstrip('/')}/models/{model}", json=payload) as response:
                if response.status == 404:
                    raise ModelNotFoundError(f"Model not found: {model}")
                await raise_for_status(response)
                if stream:
                    first = True
                    is_special = False
                    async for line in response.iter_lines():
                        if line.startswith(b"data:"):
                            data = json.loads(line[5:])
                            if "error" in data:
                                raise ResponseError(data["error"])
                            if not data["token"]["special"]:
                                chunk = data["token"]["text"]
                                if first and not do_continue:
                                    first = False
                                    chunk = chunk.lstrip()
                                if chunk:
                                    yield chunk
                            else:
                                is_special = True
                    debug.log(f"Special token: {is_special}")
                    yield FinishReason("stop" if is_special else "length")
                else:
                    async for chunk in save_response_media(response, inputs, [aspect_ratio, model]):
                        yield chunk
                        return
                    yield (await response.json())[0]["generated_text"].strip()