async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        media: MediaListType = None,
        prompt: str = None,
        proxy: str = None,
        cookies: Cookies = None,
        api_key: str = None,
        zerogpu_uuid: str = "[object Object]",
        return_conversation: bool = True,
        conversation: JsonConversation = None,
        seed: int = None,
        **kwargs
    ) -> AsyncResult:
        if model and "janus" not in model:
            raise ModelNotFoundError(f"Model '{model}' not found. Available models: {', '.join(cls.models)}")
        method = "post"
        if model == cls.default_image_model or prompt is not None:
            method = "image"
        prompt = format_prompt(messages) if prompt is None and conversation is None else prompt
        prompt = format_media_prompt(messages, prompt)
        if seed is None:
            seed = random.randint(1000, 999999)

        session_hash = uuid.uuid4().hex if conversation is None else getattr(conversation, "session_hash", uuid.uuid4().hex)
        async with StreamSession(proxy=proxy, impersonate="chrome") as session:
            if api_key is None:
                zerogpu_uuid, api_key = await get_zerogpu_token(cls.space, session, conversation, cookies)
            if conversation is None or not hasattr(conversation, "session_hash"):
                conversation = JsonConversation(session_hash=session_hash, zerogpu_token=api_key, zerogpu_uuid=zerogpu_uuid)
            else:
                conversation.zerogpu_token = api_key
            if return_conversation:
                yield conversation

            media = list(merge_media(media, messages))
            if media:
                data = FormData()
                for i in range(len(media)):
                    media[i] = (to_bytes(media[i][0]), media[i][1])
                for image, image_name in media:
                    data.add_field(f"files", image, filename=image_name)
                async with session.post(f"{cls.api_url}/gradio_api/upload", params={"upload_id": session_hash}, data=data) as response:
                    await raise_for_status(response)
                    image_files = await response.json()
                media = [{
                    "path": image_file,
                    "url": f"{cls.api_url}/gradio_api/file={image_file}",
                    "orig_name": media[i][1],
                    "size": len(media[i][0]),
                    "mime_type": is_accepted_format(media[i][0]),
                    "meta": {
                        "_type": "gradio.FileData"
                    }
                } for i, image_file in enumerate(image_files)]

            async with cls.run(method, session, prompt, conversation, None if not media else media.pop(), seed) as response:
                await raise_for_status(response)

            async with cls.run("get", session, prompt, conversation, None, seed) as response:
                response: StreamResponse = response
                counter = 3
                async for line in response.iter_lines():
                    decoded_line = line.decode(errors="replace")
                    if decoded_line.startswith('data: '):
                        try:
                            json_data = json.loads(decoded_line[6:])
                            if json_data.get('msg') == 'log':
                                yield Reasoning(status=json_data["log"])

                            if json_data.get('msg') == 'progress':
                                if 'progress_data' in json_data:
                                    if json_data['progress_data']:
                                        progress = json_data['progress_data'][0]
                                        yield Reasoning(status=f"{progress['desc']} {progress['index']}/{progress['length']}")
                                    else:
                                        yield Reasoning(status=f"Generating")

                            elif json_data.get('msg') == 'heartbeat':
                                yield Reasoning(status=f"Generating{''.join(['.' for i in range(counter)])}")
                                counter  += 1

                            elif json_data.get('msg') == 'process_completed':
                                if 'output' in json_data and 'error' in json_data['output']:
                                    json_data['output']['error'] = json_data['output']['error'].split(" <a ")[0]
                                    raise ResponseError("Missing images input" if json_data['output']['error'] and "AttributeError" in json_data['output']['error'] else json_data['output']['error'])
                                if 'output' in json_data and 'data' in json_data['output']:
                                    yield Reasoning(status="")
                                    if "image" in json_data['output']['data'][0][0]:
                                        yield ImageResponse([image["image"]["url"] for image in json_data['output']['data'][0]], prompt)
                                    else:
                                        yield json_data['output']['data'][0]
                                break

                        except json.JSONDecodeError:
                            debug.log("Could not parse JSON:", decoded_line)