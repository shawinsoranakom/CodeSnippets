async def create_async_generator(
        cls, 
        model: str, 
        messages: Messages,
        prompt: str = None,
        proxy: str = None,
        aspect_ratio: str = "1:1",
        width: int = None,
        height: int = None,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 28,
        seed: int = 0,
        randomize_seed: bool = True,
        cookies: dict = None,
        api_key: str = None,
        zerogpu_uuid: str = "[object Object]",
        **kwargs
    ) -> AsyncResult:
        async with StreamSession(impersonate="chrome", proxy=proxy) as session:
            prompt = format_media_prompt(messages, prompt)
            data = use_aspect_ratio({"width": width, "height": height}, aspect_ratio)
            data = [prompt, seed, randomize_seed, data.get("width"), data.get("height"), guidance_scale, num_inference_steps]
            conversation = JsonConversation(zerogpu_token=api_key, zerogpu_uuid=zerogpu_uuid, session_hash=uuid.uuid4().hex)
            if conversation.zerogpu_token is None:
                conversation.zerogpu_uuid, conversation.zerogpu_token = await get_zerogpu_token(cls.space, session, conversation, cookies)
            async with cls.run(f"post", session, conversation, data) as response:
                await raise_for_status(response)
                assert (await response.json()).get("event_id")
                async with cls.run("get", session, conversation) as event_response:
                    await raise_for_status(event_response)
                    async for chunk in event_response.iter_lines():
                        if chunk.startswith(b"data: "):
                            try:
                                json_data = json.loads(chunk[6:])
                                if json_data is None:
                                    continue
                                if json_data.get('msg') == 'log':
                                    yield Reasoning(status=json_data["log"])

                                if json_data.get('msg') == 'progress':
                                    if 'progress_data' in json_data:
                                        if json_data['progress_data']:
                                            progress = json_data['progress_data'][0]
                                            yield Reasoning(status=f"{progress['desc']} {progress['index']}/{progress['length']}")
                                        else:
                                            yield Reasoning(status=f"Generating")

                                elif json_data.get('msg') == 'process_generating':
                                    for item in json_data['output']['data'][0]:
                                        if isinstance(item, dict) and "url" in item:
                                            yield ImagePreview(item["url"], prompt)
                                        elif isinstance(item, list) and len(item) > 2 and "url" in item[1]:
                                            yield ImagePreview(item[2], prompt)

                                elif json_data.get('msg') == 'process_completed':
                                    if 'output' in json_data and 'error' in json_data['output']:
                                        json_data['output']['error'] = json_data['output']['error'].split(" <a ")[0]
                                        raise ResponseError(json_data['output']['error'])
                                    if 'output' in json_data and 'data' in json_data['output']:
                                        yield Reasoning(status="")
                                        if len(json_data['output']['data']) > 0:
                                            yield ImageResponse(json_data['output']['data'][0]["url"], prompt)
                                    break
                            except (json.JSONDecodeError, KeyError, TypeError) as e:
                                raise RuntimeError(f"Failed to parse message: {chunk.decode(errors='replace')}", e)