async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        stream: bool = True,
        image: ImageType = None,
        image_name: str = None,
        proxy: str = None,
        timeout: int = 240,
        chat_mode: str = "default",
        cookies: Cookies = None,
        **kwargs,
    ) -> AsyncResult:
        if image is not None or model == cls.default_vision_model:
            chat_mode = "agent"
        elif not model or model == cls.default_model:
            ...
        elif model.startswith("dall-e"):
            chat_mode = "create"
            messages = [messages[-1]]
        else:
            chat_mode = "custom"
            model = cls.get_model(model)
        if cookies is None and chat_mode != "default":
            try:
                cookies = get_cookies(".you.com")
            except MissingRequirementsError:
                pass
            if not cookies or "afUserId" not in cookies:
                browser, stop_browser = await get_nodriver(proxy=proxy)
                try:
                    page = await browser.get(cls.url)
                    await page.wait_for('[data-testid="user-profile-button"]', timeout=900)
                    cookies = {}
                    for c in await page.send(nodriver.cdp.network.get_cookies([cls.url])):
                        cookies[c.name] = c.value
                    await page.close()
                finally:
                    await stop_browser()
        async with StreamSession(
            proxy=proxy,
            impersonate="chrome",
            timeout=(30, timeout)
        ) as session:
            upload = ""
            if image is not None:
                upload_file = await cls.upload_file(
                    session, cookies,
                    to_bytes(image), image_name
                )
                upload = json.dumps([upload_file])
            headers = {
                "Accept": "text/event-stream",
                "Referer": f"{cls.url}/api/streamingSearch",
            }
            data = {
                "userFiles": upload,
                "q": format_prompt(messages),
                "domain": "youchat",
                "selectedChatMode": chat_mode,
                "conversationTurnId": str(uuid.uuid4()),
                "chatId": str(uuid.uuid4()),
            }
            if chat_mode == "custom":
                if debug.logging:
                    print(f"You model: {model}")
                data["selectedAiModel"] = model.replace("-", "_")

            async with session.get(
                f"{cls.url}/api/streamingSearch",
                params=data,
                headers=headers,
                cookies=cookies
            ) as response:
                await raise_for_status(response)
                async for line in response.iter_lines():
                    if line.startswith(b'event: '):
                        event = line[7:].decode()
                    elif line.startswith(b'data: '):
                        if event == "error":
                            raise ResponseError(line[6:])
                        if event in ["youChatUpdate", "youChatToken"]:
                            data = json.loads(line[6:])
                        if event == "youChatToken" and event in data and data[event]:
                            if data[event].startswith("#### You\'ve hit your free quota for the Model Agent. For more usage of the Model Agent, learn more at:"):
                                continue
                            yield data[event]
                        elif event == "youChatUpdate" and "t" in data and data["t"]:
                            if chat_mode == "create":
                                match = re.search(r"!\[(.+?)\]\((.+?)\)", data["t"])
                                if match:
                                    if match.group(1) == "fig":
                                        yield ImagePreview(match.group(2), messages[-1]["content"])
                                    else:
                                        yield ImageResponse(match.group(2), match.group(1))
                                else:
                                    yield data["t"]
                            else:
                                yield data["t"]