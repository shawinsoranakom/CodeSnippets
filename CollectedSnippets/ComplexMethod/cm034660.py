async def create_authed(
        cls,
        model: str,
        messages: Messages,
        auth_result: AuthResult,
        proxy: str = None,
        timeout: int = 30,
        prompt: str = None,
        media: MediaListType = None,
        conversation: BaseConversation = None,
        return_conversation: bool = True,
        **kwargs
    ) -> AsyncResult:
        if not has_curl_cffi:
            raise MissingRequirementsError('Install or update "curl_cffi" package | pip install -U curl_cffi')
        model = cls.get_model(model)
        websocket_url = cls.websocket_url + f"&clientSessionId={uuid.uuid4()}"
        headers = DEFAULT_HEADERS.copy()
        headers["origin"] = cls.url
        headers["referer"] = cls.url + "/"
        if getattr(auth_result, "access_token", None):
            websocket_url = f"{websocket_url}&accessToken={quote(auth_result.access_token)}" + (f"&X-UserIdentityType={quote(auth_result.useridentitytype)}" if getattr(auth_result, "useridentitytype", None) else "")
            headers["authorization"] = f"Bearer {auth_result.access_token}"

        async with AsyncSession(
            timeout=timeout,
            proxy=proxy,
            impersonate="chrome",
            headers=headers,
            cookies=auth_result.cookies
        ) as session:
            if conversation is None:
                # har_file = os.path.join(os.path.dirname(__file__), "copilot", "copilot.microsoft.com.har")
                # with open(har_file, "r") as f:
                #     har_entries = json.load(f).get("log", {}).get("entries", [])
                # conversationId = ""
                # for har_entry in har_entries:
                #     if har_entry.get("request"):
                #         if "/c/api/" in har_entry.get("request").get("url", ""):
                #             try:
                #                 response = await getattr(session, har_entry.get("request").get("method").lower())(
                #                     har_entry.get("request").get("url", "").replace("cvqBJw7kyPAp1RoMTmzC6", conversationId),
                #                     data=har_entry.get("request").get("postData", {}).get("text"),
                #                     headers={header["name"]: header["value"] for header in har_entry.get("request").get("headers")}
                #                 )
                #                 response.raise_for_status()
                #                 if response.headers.get("content-type", "").startswith("application/json"):
                #                     conversationId = response.json().get("currentConversationId", conversationId)
                #             except Exception as e:
                #                 debug.log(f"Copilot: Failed request to {har_entry.get('request').get('url', '')}: {e}")
                data = {
                    "timeZone": "America/Los_Angeles",
                    "startNewConversation": True,
                    "teenSupportEnabled": True,
                    "correctPersonalizationSetting": True,
                    "performUserMerge": True,
                    "deferredDataUseCapable": True
                }
                response = await session.post(
                    "https://copilot.microsoft.com/c/api/start",
                    headers={
                        "content-type": "application/json",
                        **({"x-useridentitytype": auth_result.useridentitytype} if getattr(auth_result, "useridentitytype", None) else {}),
                        **(headers or {})
                    },
                    json=data
                )
                if response.status_code == 401:
                    raise MissingAuthError("Status 401: Invalid session")
                response.raise_for_status()
                debug.log(f"Copilot: Update cookies: [{', '.join(key for key in response.cookies)}]")
                auth_result.cookies.update({key: value for key, value in response.cookies.items()})
                if not getattr(auth_result, "access_token", None) and not cls.needs_auth and cls.anon_cookie_name not in auth_result.cookies:
                    raise MissingAuthError(f"Missing cookie: {cls.anon_cookie_name}")
                conversation = Conversation(response.json().get("currentConversationId"))
                debug.log(f"Copilot: Created conversation: {conversation.conversation_id}")
            else:
                debug.log(f"Copilot: Use conversation: {conversation.conversation_id}")

            # response = await session.get("https://copilot.microsoft.com/c/api/user?api-version=4", headers={"x-useridentitytype": useridentitytype} if cls._access_token else {})
            # if response.status_code == 401:
            #     raise MissingAuthError("Status 401: Invalid session")
            # response.raise_for_status()
            # print(response.json())
            # user = response.json().get('firstName')
            # if user is None:
            #     if cls.needs_auth:
            #         raise MissingAuthError("No user found, please login first")
            #     cls._access_token = None
            # else:
            #     debug.log(f"Copilot: User: {user}")

            uploaded_attachments = []
            if auth_result.access_token:
                # Upload regular media (images)
                for media, _ in merge_media(media, messages):
                    if not isinstance(media, str):
                        data = to_bytes(media)
                        response = await session.post(
                            "https://copilot.microsoft.com/c/api/attachments",
                            headers={
                                "content-type": is_accepted_format(data),
                                "content-length": str(len(data)),
                                **({"x-useridentitytype": auth_result.useridentitytype} if getattr(auth_result, "useridentitytype", None) else {})
                            },
                            data=data
                        )
                        response.raise_for_status()
                        media = response.json().get("url")
                    uploaded_attachments.append({"type":"image", "url": media})

                # Upload bucket files
                bucket_items = extract_bucket_items(messages)
                for item in bucket_items:
                    try:
                        # Handle plain text content from bucket
                        bucket_path = Path(get_bucket_dir(item["bucket_id"]))
                        for text_chunk in read_bucket(bucket_path):
                            if text_chunk.strip():
                                # Upload plain text as a text file
                                text_data = text_chunk.encode('utf-8')
                                data = CurlMime()
                                data.addpart("file", filename=f"bucket_{item['bucket_id']}.txt", content_type="text/plain", data=text_data)
                                response = await session.post(
                                    "https://copilot.microsoft.com/c/api/attachments",
                                    multipart=data,
                                    headers={"x-useridentitytype": auth_result.useridentitytype} if getattr(auth_result, "useridentitytype", None) else {}
                                )
                                response.raise_for_status()
                                data = response.json()
                                uploaded_attachments.append({"type": "document", "attachmentId": data.get("id")})
                                debug.log(f"Copilot: Uploaded bucket text content: {item['bucket_id']}")
                            else:
                                debug.log(f"Copilot: No text content found in bucket: {item['bucket_id']}")
                    except Exception as e:
                        debug.log(f"Copilot: Failed to upload bucket item: {item}")
                        debug.error(e)

            if prompt is None:
                prompt = get_last_user_message(messages, False)

            wss = await session.ws_connect(websocket_url, timeout=3)
            if "Think" in model:
                mode = "reasoning"
            elif model.startswith("gpt-5") or "GPT-5" in model:
                mode = "smart"
            else:
                mode = "chat"
            await wss.send(json.dumps({
                "event": "send",
                "conversationId": conversation.conversation_id,
                "content": [*uploaded_attachments, {
                    "type": "text",
                    "text": prompt,
                }],
                "mode": mode,
            }).encode(), CurlWsFlag.TEXT)

            done = False
            msg = None
            image_prompt: str = None
            last_msg = None
            sources = {}
            while not wss.closed:
                try:
                    msg_txt, _ = await asyncio.wait_for(wss.recv(), 1 if done else timeout)
                    msg = json.loads(msg_txt)
                except Exception:
                    break
                last_msg = msg
                if msg.get("event") == "appendText":
                    yield msg.get("text")
                elif msg.get("event") == "generatingImage":
                    image_prompt = msg.get("prompt")
                elif msg.get("event") == "imageGenerated":
                    yield ImageResponse(msg.get("url"), image_prompt, {"preview": msg.get("thumbnailUrl")})
                elif msg.get("event") == "done":
                    yield FinishReason("stop")
                    done = True
                elif msg.get("event") == "suggestedFollowups":
                    yield SuggestedFollowups(msg.get("suggestions"))
                    break
                elif msg.get("event") == "replaceText":
                    yield msg.get("text")
                elif msg.get("event") == "titleUpdate":
                    yield TitleGeneration(msg.get("title"))
                elif msg.get("event") == "citation":
                    sources[msg.get("url")] = msg
                    yield SourceLink(list(sources.keys()).index(msg.get("url")), msg.get("url"))
                elif msg.get("event") == "partialImageGenerated":
                    mime_type = is_accepted_format(base64.b64decode(msg.get("content")[:12]))
                    yield ImagePreview(f"data:{mime_type};base64,{msg.get('content')}", image_prompt)
                elif msg.get("event") == "chainOfThought":
                    yield Reasoning(msg.get("text"))
                elif msg.get("event") == "error":
                    raise RuntimeError(f"Error: {msg}")
                elif msg.get("event") not in ["received", "startMessage", "partCompleted", "connected"]:
                    debug.log(f"Copilot Message: {msg_txt[:100]}...")
            if not done:
                raise MissingAuthError(f"Invalid response: {last_msg}")
            if return_conversation:
                yield conversation
            if sources:
                yield Sources(sources.values())
            if not wss.closed:
                await wss.close()