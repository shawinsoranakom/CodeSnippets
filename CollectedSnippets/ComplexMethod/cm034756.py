async def create_authed(
        cls,
        model: str,
        messages: Messages,
        auth_result: AuthResult,
        prompt: str = None,
        media: MediaListType = None,
        return_conversation: bool = True,
        conversation: Conversation = None,
        web_search: bool = False,
        **kwargs
    ) -> AsyncResult:
        if not has_curl_cffi:
            raise MissingRequirementsError('Install "curl_cffi" package | pip install -U curl_cffi')
        if not model and media is not None:
            model = cls.default_vision_model
        model = cls.get_model(model)

        session = Session(**auth_result.get_dict())

        if conversation is None or not hasattr(conversation, "models"):
            conversation = Conversation({})

        if model not in conversation.models:
            conversationId = cls.create_conversation(session, model)
            debug.log(f"Conversation created: {json.dumps(conversationId[8:] + '...')}")
            messageId = cls.fetch_message_id(session, conversationId)
            conversation.models[model] = {"conversationId": conversationId, "messageId": messageId}
            inputs = format_prompt(messages)
        else:
            conversationId = conversation.models[model]["conversationId"]
            conversation.models[model]["messageId"] = cls.fetch_message_id(session, conversationId)
            inputs = get_last_user_message(messages)
        if return_conversation:
            yield conversation
        settings = {
            "inputs": inputs,
            "id": conversation.models[model]["messageId"],
            "is_retry": False,
            "is_continue": False,
            "web_search": web_search,
            "tools": ["000000000000000000000001"] if model in cls.image_models else [],
        }

        headers = {
            'accept': '*/*',
            'origin': cls.origin,
            'referer': f'{cls.url}/conversation/{conversationId}',
        }
        data = CurlMime()
        data.addpart('data', data=json.dumps(settings, separators=(',', ':')))
        for image, filename in merge_media(media, messages):
            data.addpart(
                "files",
                filename=f"base64;{filename}",
                data=base64.b64encode(to_bytes(image))
            )

        response = session.post(
            f'{cls.url}/conversation/{conversationId}',
            headers=headers,
            multipart=data,
            stream=True
        )
        raise_for_status(response)

        sources = None
        for line in response.iter_lines():
            if not line:
                continue
            try:
                line = json.loads(line)
            except json.JSONDecodeError as e:
                debug.error(f"Failed to decode JSON: {line}, error: {e}")
                continue
            if "type" not in line:
                raise RuntimeError(f"Response: {line}")
            elif line["type"] == "stream":
                yield line["token"].replace('\u0000', '')
            elif line["type"] == "finalAnswer":
                if sources is not None:
                    yield sources
                yield FinishReason("stop")
                break
            elif line["type"] == "file":
                url = f"{cls.url}/conversation/{conversationId}/output/{line['sha']}"
                yield ImageResponse(url, format_media_prompt(messages, prompt), options={"cookies": auth_result.cookies})
            elif line["type"] == "webSearch" and "sources" in line:
                sources = Sources(line["sources"])
            elif line["type"] == "title":
                yield TitleGeneration(line["title"])
            elif line["type"] == "reasoning":
                yield Reasoning(line.get("token"), status=line.get("status"))