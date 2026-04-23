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
        **kwargs
    ) -> AsyncResult:
        prompt = format_prompt(messages) if prompt is None and conversation is None else prompt
        prompt = format_media_prompt(messages, prompt)

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

            if media is not None:
                data = FormData()
                mime_types = [None for i in range(len(media))]
                for i in range(len(media)):
                    mime_types[i] = is_data_an_audio(media[i][0], media[i][1])
                    media[i] = (to_bytes(media[i][0]), media[i][1])
                    mime_types[i] = is_accepted_format(media[i][0]) if mime_types[i] is None else mime_types[i]
                for image, image_name in media:
                    data.add_field(f"files", to_bytes(image), filename=image_name)
                async with session.post(f"{cls.api_url}/gradio_api/upload", params={"upload_id": session_hash}, data=data) as response:
                    await raise_for_status(response)
                    image_files = await response.json()
                media = [{
                    "path": image_file,
                    "url": f"{cls.api_url}/gradio_api/file={image_file}",
                    "orig_name": media[i][1],
                    "size": len(media[i][0]),
                    "mime_type": mime_types[i],
                    "meta": {
                        "_type": "gradio.FileData"
                    }
                } for i, image_file in enumerate(image_files)]


            async with cls.run("predict", session, prompt, conversation, media) as response:
                await raise_for_status(response)

            async with cls.run("post", session, prompt, conversation, media) as response:
                await raise_for_status(response)

            async with cls.run("get", session, prompt, conversation) as response:
                response: StreamResponse = response
                async for line in response.iter_lines():
                    if line.startswith(b'data: '):
                        try:
                            json_data = json.loads(line[6:])
                            if json_data.get('msg') == 'process_completed':
                                if 'output' in json_data and 'error' in json_data['output']:
                                    raise ResponseError(json_data['output']['error'])
                                if 'output' in json_data and 'data' in json_data['output']:
                                    yield json_data['output']['data'][0][-1]["content"]
                                break

                        except json.JSONDecodeError:
                            debug.log("Could not parse JSON:", line.decode(errors="replace"))