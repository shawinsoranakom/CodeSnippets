async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        cookies: Cookies = None,
        connector: BaseConnector = None,
        media: MediaListType = None,
        return_conversation: bool = True,
        conversation: Conversation = None,
        language: str = "en",
        prompt: str = None,
        audio: dict = None,
        **kwargs
    ) -> AsyncResult:
        if model in cls.model_aliases:
            model = cls.model_aliases[model]
        if audio is not None or model == "gemini-audio":
            prompt = format_media_prompt(messages, prompt)
            filename = get_filename(["gemini"], prompt, ".ogx", prompt)
            ensure_media_dir()
            path = os.path.join(get_media_dir(), filename)
            with open(path, "wb") as f:
                async for chunk in cls.synthesize({"text": prompt}, proxy):
                    f.write(chunk)
            yield AudioResponse(f"/media/{filename}", text=prompt)
            return
        cls._cookies = cookies or cls._cookies or get_cookies(GOOGLE_COOKIE_DOMAIN, False, True)
        if conversation is not None and getattr(conversation, "model", None) != model:
            conversation = None
        prompt = format_prompt(messages) if conversation is None else get_last_user_message(messages)
        base_connector = get_connector(connector, proxy)

        async with ClientSession(
            headers=REQUEST_HEADERS,
            connector=base_connector
        ) as session:
            if not cls._snlm0e:
                await cls.fetch_snlm0e(session, cls._cookies) if cls._cookies else None
            if not cls._snlm0e:
                try:
                    async for chunk in cls.login_generator(proxy):
                        yield chunk
                except Exception as e:
                    raise MissingAuthError('Missing or invalid "__Secure-1PSID" cookie', e)
            if not cls._snlm0e:
                if cls._cookies is None or "__Secure-1PSID" not in cls._cookies:
                    raise MissingAuthError('Missing "__Secure-1PSID" cookie')
                await cls.fetch_snlm0e(session, cls._cookies)
            if not cls._snlm0e:
                raise RuntimeError("Invalid cookies. SNlM0e not found")
            if GOOGLE_SID_COOKIE in cls._cookies:
                task = cls.rotate_tasks.get(cls._cookies[GOOGLE_SID_COOKIE])
                if not task:
                    cls.rotate_tasks[cls._cookies[GOOGLE_SID_COOKIE]] = asyncio.create_task(
                        cls.start_auto_refresh()
                    )

            uploads = await cls.upload_images(base_connector, merge_media(media, messages))
            async with ClientSession(
                cookies=cls._cookies,
                headers=REQUEST_HEADERS,
                connector=base_connector,
            ) as client:
                params = {
                    'bl': REQUEST_BL_PARAM,
                    'hl': language,
                    '_reqid': random.randint(1111, 9999),
                    'rt': 'c',
                    "f.sid": cls._sid,
                }
                data = {
                    'at': cls._snlm0e,
                    'f.req': json.dumps([None, json.dumps(cls.build_request(
                        prompt,
                        language=language,
                        conversation=conversation,
                        uploads=uploads
                    ))])
                }
                async with client.post(
                    REQUEST_URL,
                    data=data,
                    params=params,
                    headers=models[model] if model in models else None
                ) as response:
                    await raise_for_status(response)
                    image_prompt = response_part = None
                    last_content = ""
                    youtube_ids = []
                    for line in (await response.text()).split("\n"):
                        try:
                            try:
                                line = json.loads(line)
                            except ValueError:
                                continue
                            if not isinstance(line, list):
                                continue
                            yield JsonResponse(data=line, model=model)
                            if not line or len(line[0]) < 3 or not line[0][2]:
                                continue
                            response_part = json.loads(line[0][2])
                            yield JsonResponse(data=response_part, model=model)
                            if len(response_part) > 2 and isinstance(response_part[2], dict) and response_part[2].get("11"):
                                yield TitleGeneration(response_part[2].get("11"))
                            if len(response_part) < 5:
                                continue
                            if return_conversation:
                                yield Conversation(response_part[1][0], response_part[1][1], response_part[4][0][0], model)
                            def find_youtube_ids(content: str):
                                pattern = re.compile(r"http://www.youtube.com/watch\?v=([\w-]+)")
                                for match in pattern.finditer(content):
                                    if match.group(1) not in youtube_ids:
                                        yield match.group(1)
                            def read_recusive(data):
                                for item in data:
                                    if isinstance(item, list):
                                        yield from read_recusive(item)
                                    elif isinstance(item, str) and not item.startswith("rc_"):
                                        yield item
                            def find_str(data, skip=0):
                                for item in read_recusive(data):
                                    if skip > 0:
                                        skip -= 1
                                        continue
                                    yield item
                            if response_part[4]:
                                reasoning = "\n\n".join(find_str(response_part[4][0], 3))
                                reasoning = re.sub(r"<b>|</b>", "**", reasoning)
                                def replace_image(match):
                                    return f"![](https:{match.group(0)})"
                                reasoning = re.sub(r"//yt3.(?:ggpht.com|googleusercontent.com/ytc)/[\w=-]+", replace_image, reasoning)
                                reasoning = re.sub(r"\nyoutube\n", "\n\n\n", reasoning)
                                reasoning = re.sub(r"\nyoutube_tool\n", "\n\n", reasoning)
                                reasoning = re.sub(r"\nYouTube\n", "\nYouTube ", reasoning)
                                reasoning = reasoning.replace('\nhttps://www.gstatic.com/images/branding/productlogos/youtube/v9/192px.svg', '<i class="fa-brands fa-youtube"></i>')
                                youtube_ids = list(find_youtube_ids(reasoning))
                                content = response_part[4][0][1][0]
                                if reasoning:
                                    yield Reasoning(reasoning, status="🤔")
                        except (ValueError, KeyError, TypeError, IndexError) as e:
                            if kwargs.get("debug_mode", False):
                                raise e
                            debug.error(f"{cls.__name__} {type(e).__name__}: {e}")
                            continue
                        match = re.search(r'\[Imagen of (.*?)\]', content)
                        if match:
                            image_prompt = match.group(1)
                            content = content.replace(match.group(0), '')
                        pattern = r"http://googleusercontent.com/(?:image_generation|youtube|map)_content/\d+"
                        content = re.sub(pattern, "", content)
                        content = content.replace("<!-- end list -->", "")
                        content = content.replace("<ctrl94>thought", "<think>").replace("<ctrl95>", "</think>")
                        def replace_link(match):
                            return f"(https://{quote_plus(unquote_plus(match.group(1)), '/?&=#')})"
                        content = re.sub(r"\(https://www.google.com/(?:search\?q=|url\?sa=E&source=gmail&q=)https?://(.+?)\)", replace_link, content)

                        if last_content and content.startswith(last_content):
                            yield content[len(last_content):]
                        else:
                            yield content
                        last_content = content
                        if image_prompt:
                            try:
                                images = [image[0][3][3] for image in response_part[4][0][12][7][0]]
                                image_prompt = image_prompt.replace("a fake image", "")
                                yield ImageResponse(images, image_prompt, {"cookies": cls._cookies})
                            except (TypeError, IndexError, KeyError):
                                pass
                        youtube_ids = youtube_ids if youtube_ids else find_youtube_ids(content)
                        if youtube_ids:
                            yield YouTubeResponse(youtube_ids)