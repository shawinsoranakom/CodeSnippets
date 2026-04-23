async def create_authed(
        cls,
        model: str,
        messages: Messages,
        auth_result: AuthResult,
        proxy: str = None,
        timeout: int = 360,
        auto_continue: bool = False,
        action: Optional[str] = None,
        conversation: Conversation = None,
        media: MediaListType = None,
        return_conversation: bool = True,
        web_search: bool = False,
        prompt: str = None,
        conversation_mode: Optional[dict] = None,
        temporary: Optional[bool] = None,
        conversation_id: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        **kwargs
    ) -> AsyncResult:
        """
        Create an asynchronous generator for the conversation.

        Args:
            model (str): The model name.
            messages (Messages): The list of previous messages.
            proxy (str): Proxy to use for requests.
            timeout (int): Timeout for requests.
            api_key (str): Access token for authentication.
            auto_continue (bool): Flag to automatically continue the conversation.
            action (str): Type of action ('next', 'continue', 'variant').
            media (MediaListType): Images to include in the conversation.
            return_conversation (bool): Flag to include response fields in the output.
            **kwargs: Additional keyword arguments.

        Yields:
            AsyncResult: Asynchronous results from the generator.

        Raises:
            RuntimeError: If an error occurs during processing.
        """
        if temporary is None:
            temporary = action is not None and conversation_id is None
        if action is None:
            action = "next"
        async with StreamSession(
            proxy=proxy,
            impersonate="chrome",
            timeout=timeout
        ) as session:
            image_requests = None
            media = merge_media(media, messages)
            if not cls.needs_auth and not media:
                if cls._headers is None:
                    cls._create_request_args(cls._cookies)
                    async with session.get(cls.url, headers=INIT_HEADERS) as response:
                        cls._update_request_args(auth_result, session)
                        await raise_for_status(response)
            else:
                if cls._headers is None and getattr(auth_result, "cookies", None):
                    cls._create_request_args(auth_result.cookies, auth_result.headers)
                if not cls._set_api_key(getattr(auth_result, "api_key", None)):
                    raise MissingAuthError("Access token is not valid")
                async with session.get(cls.url, headers=cls._headers) as response:
                    cls._update_request_args(auth_result, session)
                    await raise_for_status(response)

                # try:
                image_requests = await cls.upload_files(session, auth_result, media)
                # except Exception as e:
                #     debug.error("OpenaiChat: Upload image failed")
                #     debug.error(e)
            try:
                model = cls.get_model(model)
            except ModelNotFoundError:
                pass
            image_model = False
            if model in cls.image_models:
                image_model = True
                model = cls.default_model
            if conversation is None:
                conversation = Conversation(None, str(uuid.uuid4()), getattr(auth_result, "cookies", {}).get("oai-did"))
            else:
                conversation = copy(conversation)

            if conversation_mode is None:
                _gizmo_id = kwargs.get("gizmo_id")
                if _gizmo_id:
                    conversation_mode = {"kind": "gizmo_interaction", "gizmo_id": _gizmo_id}
                else:
                    conversation_mode = {"kind": "primary_assistant"}

            if getattr(auth_result, "cookies", {}).get("oai-did") != getattr(conversation, "user_id", None):
                conversation = Conversation(None, str(uuid.uuid4()))
            if cls._api_key is None:
                auto_continue = False
            conversation.finish_reason = None
            sources = OpenAISources([])
            references = ContentReferences()
            system_hints = ["picture_v2"] if image_model else []
            if reasoning_effort == "high":
                system_hints.append("reason")
            if web_search:
                system_hints.append("search")
            while conversation.finish_reason is None:
                conduit_token = None
                if cls._api_key is not None:
                    data = {
                        "action": "next",
                        "fork_from_shared_post": False,
                        "parent_message_id": conversation.message_id,
                        "model": model,
                        "timezone_offset_min": -120,
                        "timezone": "Europe/Berlin",
                        "conversation_mode": conversation_mode,
                        "system_hints": system_hints,
                        "supports_buffering": True,
                        "supported_encodings": ["v1"]
                    }
                    if temporary:
                        data["history_and_training_disabled"] = True
                    if conversation.conversation_id is not None and not temporary:
                        data["conversation_id"] = conversation.conversation_id
                    async with session.post(
                        prepare_url,
                        json=data,
                        headers=cls._headers
                    ) as response:
                        await raise_for_status(response)
                        conduit_token = (await response.json())["conduit_token"]
                async with session.post(
                    f"{cls.url}/backend-anon/sentinel/chat-requirements"
                    if cls._api_key is None else
                    f"{cls.url}/backend-api/sentinel/chat-requirements",
                    json={"p": None if not getattr(auth_result, "proof_token", None) else get_requirements_token(
                        getattr(auth_result, "proof_token", None))},
                    headers=cls._headers
                ) as response:
                    if response.status in (401, 403):
                        raise MissingAuthError(f"Response status: {response.status}")
                    else:
                        cls._update_request_args(auth_result, session)
                    await raise_for_status(response)
                    chat_requirements = await response.json()
                    need_turnstile = chat_requirements.get("turnstile", {}).get("required", False)
                    need_arkose = chat_requirements.get("arkose", {}).get("required", False)
                    chat_token = chat_requirements.get("token")

                    # if need_arkose and cls.request_config.arkose_token is None:
                #     await get_request_config(proxy)
                #     cls._create_request_args(auth_result.cookies, auth_result.headers)
                #     cls._set_api_key(auth_result.access_token)
                #     if auth_result.arkose_token is None:
                #         raise MissingAuthError("No arkose token found in .har file")
                if "proofofwork" in chat_requirements:
                    user_agent = getattr(auth_result, "headers", {}).get("user-agent")
                    proof_token = getattr(auth_result, "proof_token", None)
                    if proof_token is None:
                        auth_result.proof_token = get_config(user_agent)
                    proofofwork = generate_proof_token(
                        **chat_requirements["proofofwork"],
                        user_agent=user_agent,
                        proof_token=proof_token
                    )
                # [debug.log(text) for text in (
                # f"Arkose: {'False' if not need_arkose else auth_result.arkose_token[:12]+'...'}",
                # f"Proofofwork: {'False' if proofofwork is None else proofofwork[:12]+'...'}",
                # f"AccessToken: {'False' if cls._api_key is None else cls._api_key[:12]+'...'}",
                # )]
                data = {
                    "action": "next",
                    "parent_message_id": conversation.message_id,
                    "model": model,
                    "timezone_offset_min": -120,
                    "timezone": "Europe/Berlin",
                    "conversation_mode": conversation_mode,
                    "enable_message_followups": True,
                    "system_hints": system_hints,
                    "supports_buffering": True,
                    "supported_encodings": ["v1"],
                    "client_contextual_info": {"is_dark_mode": False, "time_since_loaded": random.randint(20, 500),
                                               "page_height": 578, "page_width": 1850, "pixel_ratio": 1,
                                               "screen_height": 1080, "screen_width": 1920},
                    "paragen_cot_summary_display_override": "allow"
                }
                if temporary:
                    data["history_and_training_disabled"] = True

                if conversation.conversation_id is not None and not temporary:
                    data["conversation_id"] = conversation.conversation_id
                    debug.log(f"OpenaiChat: Use conversation: {conversation.conversation_id}")
                prompt = conversation.prompt = format_media_prompt(messages, prompt)
                if action != "continue":
                    data["parent_message_id"] = getattr(conversation, "parent_message_id", conversation.message_id)
                    conversation.parent_message_id = None
                    new_messages = messages
                    if conversation.conversation_id is not None:
                        new_messages = []
                        for message in messages:
                            if message.get("role") == "assistant":
                                new_messages = []
                            else:
                                new_messages.append(message)
                    data["messages"] = cls.create_messages(new_messages, image_requests,
                                                           ["search"] if web_search else None)
                yield JsonRequest.from_dict(data)
                headers = {
                    **cls._headers,
                    "accept": "text/event-stream",
                    "content-type": "application/json",
                    "openai-sentinel-chat-requirements-token": chat_token,
                    **({} if conduit_token is None else {"x-conduit-token": conduit_token})
                }
                # if cls.request_config.arkose_token:
                #    headers["openai-sentinel-arkose-token"] = cls.request_config.arkose_token
                if proofofwork is not None:
                    headers["openai-sentinel-proof-token"] = proofofwork
                if need_turnstile and getattr(auth_result, "turnstile_token", None) is not None:
                    headers['openai-sentinel-turnstile-token'] = auth_result.turnstile_token
                async with session.post(
                    backend_anon_url
                    if cls._api_key is None else
                    backend_url,
                    json=data,
                    headers=headers
                ) as response:
                    cls._update_request_args(auth_result, session)
                    if response.status in (401, 403, 429, 500):
                        raise MissingAuthError("Access token is not valid")
                    elif response.status == 422:
                        raise RuntimeError((await response.json()), data)
                    await raise_for_status(response)
                    buffer = u""
                    matches = []
                    async for line in response.iter_lines():
                        pattern = re.compile(r"file-service://[\w-]+")
                        for match in pattern.finditer(line.decode(errors="ignore")):
                            if match.group(0) in matches:
                                continue
                            matches.append(match.group(0))
                            generated_image = await cls.get_generated_image(session, auth_result, match.group(0),
                                                                            prompt)
                            if generated_image is not None:
                                yield generated_image
                        async for chunk in cls.iter_messages_line(session, auth_result, line, conversation, sources,
                                                                  references):
                            if isinstance(chunk, str):
                                chunk = chunk.replace("\ue203", "").replace("\ue204", "").replace("\ue206", "")
                                buffer += chunk
                                if buffer.find(u"\ue200") != -1:
                                    if buffer.find(u"\ue201") != -1:
                                        def sequence_replacer(match):
                                            def citation_replacer(match: re.Match[str]):
                                                ref_type = match.group(1)
                                                ref_index = int(match.group(2))
                                                if ((ref_type == "image" and is_image_embedding) or
                                                        is_video_embedding or
                                                        ref_type == "forecast"):

                                                    reference = references.get_reference({
                                                        "ref_index": ref_index,
                                                        "ref_type": ref_type
                                                    })
                                                    if not reference:
                                                        return ""

                                                    if ref_type == "forecast":
                                                        if reference.get("alt"):
                                                            return reference.get("alt")
                                                        if reference.get("prompt_text"):
                                                            return reference.get("prompt_text")

                                                    if is_image_embedding and reference.get("content_url", ""):
                                                        return f"![{reference.get('title', '')}]({reference.get('content_url')})"

                                                    if is_video_embedding:
                                                        if reference.get("url", "") and reference.get("thumbnail_url",
                                                                                                      ""):
                                                            return f"[![{reference.get('title', '')}]({reference['thumbnail_url']})]({reference['url']})"
                                                        video_match = re.match(r"video\n(.*?)\nturn[0-9]+",
                                                                               match.group(0))
                                                        if video_match:
                                                            return video_match.group(1)
                                                    return ""

                                                source_index = sources.get_index({
                                                    "ref_index": ref_index,
                                                    "ref_type": ref_type
                                                })
                                                if source_index is not None and len(sources.list) > source_index:
                                                    link = sources.list[source_index]["url"]
                                                    return f"[[{source_index + 1}]]({link})"
                                                return f""

                                            def products_replacer(match: re.Match[str]):
                                                try:
                                                    products_data = json.loads(match.group(1))
                                                    products_str = ""
                                                    for idx, _ in enumerate(products_data.get("selections", []) or []):
                                                        name = products_data.get('selections', [])[idx][1]
                                                        tags = products_data.get('tags', [])[idx]
                                                        products_str += f"{name} - {tags}\n\n"

                                                    return products_str
                                                except Exception:
                                                    return ""

                                            sequence_content = match.group(1)
                                            sequence_content = sequence_content.replace("\ue200", "").replace("\ue202",
                                                                                                              "\n").replace(
                                                "\ue201", "")
                                            sequence_content = sequence_content.replace("navlist\n", "#### ")

                                            # Handle search, news, view and image citations
                                            is_image_embedding = sequence_content.startswith("i\nturn")
                                            is_video_embedding = sequence_content.startswith("video\n")
                                            sequence_content = re.sub(
                                                r'(?:cite\nturn[0-9]+|forecast\nturn[0-9]+|video\n.*?\nturn[0-9]+|i?\n?turn[0-9]+)(search|news|view|image|forecast)(\d+)',
                                                citation_replacer,
                                                sequence_content
                                            )
                                            sequence_content = re.sub(r'products\n(.*)', products_replacer,
                                                                      sequence_content)
                                            sequence_content = re.sub(r'product_entity\n\[".*","(.*)"\]',
                                                                      lambda x: x.group(1), sequence_content)
                                            return sequence_content

                                        # process only completed sequences and do not touch start of next not completed sequence
                                        buffer = re.sub(r'\ue200(.*?)\ue201', sequence_replacer, buffer,
                                                        flags=re.DOTALL)

                                        if buffer.find(u"\ue200") != -1:  # still have uncompleted sequence
                                            continue
                                    else:
                                        # do not yield to consume rest part of special sequence
                                        continue

                                yield buffer
                                buffer = ""
                            else:
                                yield chunk
                        if conversation.finish_reason is not None:
                            break
                    if buffer:
                        yield buffer
                if sources.list:
                    yield sources
                if conversation.generated_images:
                    yield ImageResponse(conversation.generated_images.urls, conversation.prompt,
                                        {"headers": auth_result.headers})
                    conversation.generated_images = None
                conversation.prompt = None
                if return_conversation:
                    yield conversation
                if auth_result.api_key is not None:
                    yield SynthesizeData(cls.__name__, {
                        "conversation_id": conversation.conversation_id,
                        "message_id": conversation.message_id,
                        "voice": "maple",
                    })
                if auto_continue and conversation.finish_reason == "max_tokens":
                    conversation.finish_reason = None
                    action = "continue"
                    await asyncio.sleep(5)
                else:
                    break

            if conversation.task and kwargs.get("wait_media", True):
                async for _m in cls.wss_media(session, conversation, auth_result.headers, auth_result):
                    yield _m
            # if kwargs.get("wait_media"):
            #     async for _m in cls.wait_media(session, conversation, headers, auth_result):
            #         yield _m

            yield FinishReason(conversation.finish_reason)