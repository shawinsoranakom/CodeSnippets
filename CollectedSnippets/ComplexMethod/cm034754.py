async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        api_key: str = None,
        extra_body: dict = None,
        prompt: str = None,
        proxy: str = None,
        timeout: int = 0,
        # Video & Image Generation
        n: int = 1,
        aspect_ratio: str = None,
        # Only for Image Generation
        height: int = None,
        width: int = None,
        # Video Generation
        resolution: str = "480p",
        **kwargs
    ):
        if not api_key:
            raise MissingAuthError('Add a "api_key"')
        if extra_body is None:
            extra_body = {}
        selected_provider = None
        if model and ":" in model:
            model, selected_provider = model.split(":", 1)
        elif not model:
            model = cls.get_models()[0]
        prompt = format_media_prompt(messages, prompt)
        provider_mapping = await cls.get_mapping(model, api_key)
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/json',
            'Prefer': 'wait',
        }
        new_mapping = {
            "hf-free" if key == "hf-inference" else key: value for key, value in provider_mapping.items()
            if key in ["replicate", "together", "hf-inference"]
        }
        provider_mapping = {**new_mapping, **provider_mapping}
        if not provider_mapping:
            raise ModelNotFoundError(f"Model is not supported: {model} in: {cls.__name__}")
        async def generate(extra_body: dict, aspect_ratio: str = None):
            last_response = None
            for provider_key, provider in provider_mapping.items():
                if selected_provider is not None and selected_provider != provider_key:
                    continue
                provider_info = ProviderInfo(**{**cls.get_dict(), "label": f"HuggingFace ({provider_key})", "url": f"{cls.url}/{model}"})

                base_url = f"https://router.huggingface.co/{provider_key}"
                task = provider["task"]
                provider_id = provider["providerId"]
                if task not in cls.tasks:
                    raise ModelNotFoundError(f"Model is not supported: {model} in: {cls.__name__} task: {task}")

                if aspect_ratio is None:
                    aspect_ratio = "1:1" if task == "text-to-image" else "16:9"
                extra_body_image = use_aspect_ratio({
                    **extra_body,
                    "height": height,
                    "width": width,
                }, aspect_ratio)
                extra_body_video = {}
                if task == "text-to-video" and provider_key != "novita":
                    extra_body_video = {
                        "num_inference_steps": 20,
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio,
                        **extra_body
                    }
                url = f"{base_url}/{provider_id}"
                data = {
                    "prompt": prompt,
                    **{"width": width, "height": height},
                    **(extra_body_video if task == "text-to-video" else extra_body_image),
                }
                if provider_key == "fal-ai" and task == "text-to-image":
                    data = {
                        "image_size": use_aspect_ratio({
                            "height": height,
                            "width": width,
                        }, aspect_ratio),
                        **extra_body
                    }
                elif provider_key == "novita":
                    url = f"{base_url}/v3/hf/{provider_id}"
                elif provider_key == "replicate":
                    url = f"{base_url}/v1/models/{provider_id}/predictions"
                    data = {
                        "input": data
                    }
                elif provider_key in ("hf-inference", "hf-free"):
                    base_url = "https://api-inference.huggingface.co"
                    url = f"{base_url}/models/{provider_id}"
                    data = {
                        "inputs": prompt,
                        "parameters": {
                            "seed": random.randint(0, 2**32),
                            **data
                        }
                    }
                elif task == "text-to-image":
                    url = f"{base_url}/v1/images/generations"
                    data = {
                        "response_format": "url",
                        "model": provider_id,
                        **data
                    }

                async with StreamSession(
                    headers=headers if provider_key == "hf-free" or api_key is None else {**headers, "Authorization": f"Bearer {api_key}"},
                    proxy=proxy,
                    timeout=timeout
                ) as session:
                    async with session.post(url, json=data) as response:
                        if response.status in (400, 401, 402):
                            last_response = response
                            debug.error(f"{cls.__name__}: Error {response.status} with {provider_key} and {provider_id}")
                            continue
                        if response.status == 404:
                            raise ModelNotFoundError(f"Model not found: {model}")
                        await raise_for_status(response)
                        if response.headers.get("Content-Type", "").startswith("application/json"):
                            result = await response.json()
                            if "video" in result:
                                return provider_info, VideoResponse(result.get("video").get("url", result.get("video").get("video_url")), prompt)
                            elif task == "text-to-image":
                                try:
                                    return provider_info, ImageResponse([
                                        item["url"] if isinstance(item, dict) else item
                                        for item in result.get("images", result.get("data", result.get("output")))
                                    ], prompt)
                                except Exception:
                                    raise ValueError(f"Unexpected response: {result}")
                            elif task == "text-to-video" and result.get("output") is not None:
                                return provider_info, VideoResponse(result["output"], prompt)
                            raise ValueError(f"Unexpected response: {result}")
                        async for chunk in save_response_media(response, prompt, [aspect_ratio, model]):
                            return provider_info, chunk

            await raise_for_status(last_response)

        background_tasks = set()
        running_tasks = set()
        started = time.time()
        while n > 0:
            n -= 1
            task = asyncio.create_task(generate(extra_body, aspect_ratio))
            background_tasks.add(task)
            running_tasks.add(task)
            task.add_done_callback(running_tasks.discard)
        while running_tasks:
            diff = time.time() - started
            if diff > 1:
                yield Reasoning(label="Generating", status=f"{diff:.2f}s")
            await asyncio.sleep(0.2)
        for task in background_tasks:
            provider_info, media_response = await task
            yield Reasoning(label="Finished", status=f"{time.time() - started:.2f}s")
            yield provider_info
            yield media_response