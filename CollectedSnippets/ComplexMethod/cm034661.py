async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        refresh_token: str = None,
        conversation: Conversation = None,
        return_conversation: bool = False,
        stream: bool = True,
        media: MediaListType = None,
        **kwargs
    ) -> AsyncResult:
        model = cls.get_model(model)

        if conversation is None:
            conversation = Conversation(refresh_token)
        elif refresh_token and not conversation.refresh_token:
            conversation.refresh_token = refresh_token

        async with ClientSession() as session:
            access_token = await cls.get_access_token(session, conversation)

            media_attachments = []
            merged_media = list(merge_media(media, messages))
            if merged_media:
                for media_data, media_name in merged_media:
                    try:
                        if isinstance(media_data, str) and media_data.startswith("data:"):
                            data_part = media_data.split(",", 1)[1]
                            media_bytes = base64.b64decode(data_part)
                        elif hasattr(media_data, 'read'):
                            media_bytes = media_data.read()
                        elif isinstance(media_data, (str, os.PathLike)):
                            with open(media_data, 'rb') as f:
                                media_bytes = f.read()
                        else:
                            media_bytes = media_data

                        image_id = await cls.upload_media(session, access_token, media_bytes, media_name)
                        media_attachments.append(image_id)
                    except Exception as e:
                        debug.log(f"OperaAria: failed to upload media '{media_name}': {e}")
                        continue

            headers = {
                "Accept": "text/event-stream" if stream else "application/json",
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Origin": "opera-aria://ui",
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36 OPR/89.0.0.0",
                "X-Opera-Timezone": "+03:00",
                "X-Opera-UI-Language": "en"
            }

            data = {
                "query": format_prompt(messages), "stream": stream, "linkify": True,
                "linkify_version": 3, "sia": True, "media_attachments": media_attachments,
                "encryption": {"key": conversation.encryption_key}
            }

            if not conversation.is_first_request and conversation.conversation_id:
                data["conversation_id"] = conversation.conversation_id

            async with session.post(cls.api_endpoint, headers=headers, json=data, proxy=proxy) as response:
                response.raise_for_status()

                if stream:
                    image_urls, finish_reason = [], None

                    async for line in response.content:
                        if not line: continue
                        decoded = line.decode('utf-8').strip()
                        if not decoded.startswith('data: '): continue

                        content = decoded[6:]
                        if content == '[DONE]': break

                        try:
                            json_data = json.loads(content)
                            if 'message' in json_data:
                                message_chunk = json_data['message']
                                found_urls = cls.extract_image_urls(message_chunk)
                                if found_urls:
                                    image_urls.extend(found_urls)
                                else:
                                    yield message_chunk

                            if 'conversation_id' in json_data and json_data['conversation_id']:
                                conversation.conversation_id = json_data['conversation_id']

                            if 'finish_reason' in json_data and json_data.get('finish_reason'):
                                finish_reason = json_data['finish_reason']

                        except json.JSONDecodeError:
                            continue

                    if image_urls:
                        yield ImageResponse(image_urls, format_prompt(messages))

                    if finish_reason:
                        yield FinishReason(finish_reason)

                else: # Non-streaming
                    json_data = await response.json()
                    if 'message' in json_data:
                        message = json_data['message']
                        image_urls = cls.extract_image_urls(message)
                        if image_urls:
                            yield ImageResponse(image_urls, format_prompt(messages))
                        else:
                            yield message

                    if 'conversation_id' in json_data and json_data['conversation_id']:
                        conversation.conversation_id = json_data['conversation_id']

                    if 'finish_reason' in json_data and json_data['finish_reason']:
                        yield FinishReason(json_data['finish_reason'])

                conversation.is_first_request = False

                if return_conversation:
                    yield conversation