async def create_async_generator(
            cls,
            model: str,
            messages: Messages,
            media: MediaListType = None,
            conversation: JsonConversation = None,
            proxy: str = None,
            stream: bool = True,
            reasoning_effort: Optional[Literal["low", "medium", "high"]] = "medium",
            chat_type: Literal[
                "t2t", "search", "artifacts", "web_dev", "deep_research", "t2i", "image_edit", "t2v"
            ] = "t2t",
            aspect_ratio: Optional[Literal["1:1", "4:3", "3:4", "16:9", "9:16"]] = None,
            **kwargs
    ) -> AsyncResult:
        """
        chat_type:
            DeepResearch = "deep_research"
            Artifacts = "artifacts"
            WebSearch = "search"
            ImageGeneration = "t2i"
            ImageEdit = "image_edit"
            VideoGeneration = "t2v"
            Txt2Txt = "t2t"
            WebDev = "web_dev"
        """
        model_name = cls.get_model(model)
        prompt = get_last_user_message(messages)
        enable_thinking = reasoning_effort in ("medium", "high")
        thinking_mode: Literal["Auto", "Thinking", "Fast"] = kwargs.get("thinking_mode",
                                                                        "Auto" if enable_thinking else "Fast")
        auto_thinking = thinking_mode == "Auto"
        timeout = kwargs.get("timeout") or 5 * 60
        token = kwargs.get("token")
        async with StreamSession(headers=cls._get_headers(token)) as session:
            if token:
                try:
                    async with session.get('https://chat.qwen.ai/api/v1/auths/', proxy=proxy) as user_info_res:
                        await cls.raise_for_status(user_info_res)
                        debug.log(await user_info_res.json())
                except Exception as e:
                    debug.error(e)
            for attempt in range(5):
                try:
                    req_headers = await cls._get_req_headers(session, proxy=proxy)
                    message_id = str(uuid.uuid4())
                    if conversation is None:
                        chat_payload = {
                            "title": "New Chat",
                            "models": [model_name],
                            "chat_mode": "normal",
                            "chat_type": chat_type,
                            "timestamp": int(time() * 1000)
                        }
                        async with session.post(
                                f'{cls.url}/api/v2/chats/new', json=chat_payload, headers=req_headers,
                                proxy=proxy
                        ) as resp:
                            await cls.raise_for_status(resp)
                            data = await resp.json()
                            if not (data.get('success') and data['data'].get('id')):
                                raise RuntimeError(f"Failed to create chat: {data}")
                        conversation = JsonConversation(
                            chat_id=data['data']['id'],
                            cookies={key: value for key, value in resp.cookies.items()},
                            parent_id=None
                        )
                    files = []
                    media = list(merge_media(media, messages))
                    if media:
                        files = await cls.prepare_files(media, session=session,
                                                        headers=req_headers)

                    feature_config = {
                        "auto_thinking": auto_thinking,
                        "thinking_mode": thinking_mode,
                        # "thinking_format": "summary",
                        "thinking_enabled": enable_thinking,
                        "output_schema": "phase",
                        # "instructions": None,
                        "research_mode": "normal",
                        "auto_search": True
                    } if enable_thinking else {
                        "thinking_enabled": enable_thinking,
                        "output_schema": "phase",
                        "thinking_budget": 81920
                    }

                    msg_payload = {
                        "stream": stream,
                        "incremental_output": stream,
                        "chat_id": conversation.chat_id,
                        "chat_mode": "normal",
                        "model": model_name,
                        "parent_id": conversation.parent_id,
                        "messages": [
                            {
                                "fid": message_id,
                                "parentId": conversation.parent_id,
                                "childrenIds": [],
                                "role": "user",
                                "content": prompt,
                                "user_action": "chat",
                                "files": files,
                                "models": [model_name],
                                "chat_type": chat_type,
                                "feature_config": feature_config,
                                "sub_chat_type": chat_type
                            }
                        ]
                    }

                    if aspect_ratio:
                        msg_payload["size"] = aspect_ratio

                    async with session.post(
                            f'{cls.url}/api/v2/chat/completions?chat_id={conversation.chat_id}',
                            json=msg_payload,
                            headers=req_headers, proxy=proxy, timeout=timeout, cookies=conversation.cookies
                    ) as resp:
                        await cls.raise_for_status(resp)
                        if resp.headers.get("content-type", "").startswith("application/json"):
                            resp_json = await resp.json()
                            if resp_json.get("success") is False or resp_json.get("data", {}).get("code"):
                                raise RuntimeError(f"Response: {resp_json}")
                        # args["cookies"] = merge_cookies(args.get("cookies"), resp)
                        thinking_started = False
                        usage = None
                        async for chunk in sse_stream(resp):
                            try:
                                if "response.created" in chunk:
                                    conversation.parent_id = chunk.get("response.created", {}).get(
                                        "response_id")
                                    yield conversation
                                error = chunk.get("error", {})
                                if error:
                                    raise ResponseError(f'{error["code"]}: {error["details"]}')
                                usage = chunk.get("usage", usage)
                                choices = chunk.get("choices", [])
                                if not choices: continue
                                delta = choices[0].get("delta", {})
                                phase = delta.get("phase")
                                content = delta.get("content")
                                status = delta.get("status")
                                extra = delta.get("extra", {})
                                if phase == "think" and not thinking_started:
                                    thinking_started = True
                                elif phase == "answer" and thinking_started:
                                    thinking_started = False
                                elif phase == "image_gen" and status == "typing":
                                    yield ImageResponse(content, prompt, extra)
                                    continue
                                elif phase == "image_gen" and status == "finished":
                                    yield FinishReason("stop")
                                if content:
                                    yield Reasoning(content) if thinking_started else content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
                        if usage:
                            yield Usage(**usage)
                        return

                except (aiohttp.ClientResponseError, RuntimeError) as e:
                    is_rate_limit = (isinstance(e, aiohttp.ClientResponseError) and e.status == 429) or \
                                    ("RateLimited" in str(e))
                    if is_rate_limit:
                        debug.log(
                            f"[Qwen] WARNING: Rate limit detected (attempt {attempt + 1}/5). Invalidating current midtoken.")
                        cls._midtoken = None
                        cls._midtoken_uses = 0
                        conversation = None
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise e
            raise RateLimitError("The Qwen provider reached the request limit after 5 attempts.")

            # except CloudflareError as e:
            #     debug.error(f"{cls.__name__}: {e}")
            #     args = await cls.get_args(proxy, **kwargs)
            #     cookie = "; ".join([f"{k}={v}" for k, v in args["cookies"].items()])
            #     continue
        raise RateLimitError("The Qwen provider reached the limit Cloudflare.")