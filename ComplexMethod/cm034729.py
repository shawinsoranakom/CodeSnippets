async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        stream: bool = True,
        api_key: str = None,
        proxy: str = None,
        cookies: Cookies = None,
        conversation_id: str = None,
        conversation: Conversation = None,
        return_conversation: bool = True,
        **kwargs
    ) -> AsyncResult:
        if not model:
            model = cls.default_model

        if cookies is None:
            cookies = get_cookies("github.com")

        async with ClientSession(
            connector=get_connector(proxy=proxy),
            cookies=cookies,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://github.com/copilot',
                'Content-Type': 'application/json',
                'GitHub-Verified-Fetch': 'true',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://github.com',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Priority': 'u=1'
            }
        ) as session:
            headers = {}
            if api_key is None:
                async with session.post("https://github.com/github-copilot/chat/token") as response:
                    await raise_for_status(response, "Get token")
                    api_key = (await response.json()).get("token")

            headers = {
                "Authorization": f"GitHub-Bearer {api_key}",
            }

            if conversation is not None:
                conversation_id = conversation.conversation_id

            if conversation_id is None:
                async with session.post(
                    "https://api.individual.githubcopilot.com/github/chat/threads", 
                    headers=headers
                ) as response:
                    await raise_for_status(response)
                    conversation_id = (await response.json()).get("thread_id")

            if return_conversation:
                yield Conversation(conversation_id)
                content = get_last_user_message(messages)
            else:
                content = format_prompt(messages)

            json_data = {
                "content": content,
                "intent": "conversation",
                "references": [],
                "context": [],
                "currentURL": f"https://github.com/copilot/c/{conversation_id}",
                "streaming": stream,
                "confirmations": [],
                "customInstructions": [],
                "model": model,
                "mode": "immersive"
            }

            async with session.post(
                f"https://api.individual.githubcopilot.com/github/chat/threads/{conversation_id}/messages",
                json=json_data,
                headers=headers
            ) as response:
                await raise_for_status(response, f"Send message with model {model}")

                if stream:
                    async for line in response.content:
                        if line.startswith(b"data: "):
                            try:
                                data = json.loads(line[6:])
                                if data.get("type") == "content":
                                    content = data.get("body", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    full_content = ""
                    async for line in response.content:
                        if line.startswith(b"data: "):
                            try:
                                data = json.loads(line[6:])
                                if data.get("type") == "content":
                                    full_content += data.get("body", "")
                            except json.JSONDecodeError:
                                continue
                    if full_content:
                        yield full_content