async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        prompt: str = None,
        proxy: str = None,
        media: MediaListType = None,
        top_p: float = None,
        temperature: float = None,
        max_tokens: int = 1024,
        conversation: Conversation = None,
        return_conversation: bool = True,
        **kwargs
    ) -> AsyncResult:      
        model = cls.get_model(model)
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.blackbox.ai',
            'referer': 'https://www.blackbox.ai/',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }

        async with ClientSession(headers=headers) as session:
            if conversation is None or not hasattr(conversation, "chat_id"):
                conversation = Conversation(model)
                conversation.validated_value = await cls.fetch_validated()
                conversation.chat_id = cls.generate_id()

            current_messages = []
            for i, msg in enumerate(render_messages(messages)):
                msg_id = conversation.chat_id if i == 0 and msg["role"] == "user" else cls.generate_id()
                current_msg = {
                    "id": msg_id,
                    "content": msg["content"],
                    "role": msg["role"]
                }
                current_messages.append(current_msg)

            media = list(merge_media(media, messages))
            if media:
                current_messages[-1]['data'] = {
                    "imagesData": [
                        {
                            "filePath": f"/{image_name}",
                            "contents": to_data_uri(image)
                        }
                        for image, image_name in media
                    ],
                    "fileText": "",
                    "title": ""
                }

            # Get session data from HAR files
            cls.session_data = cls._find_session_in_har_files() or cls.session_data

            if not cls.session_data:
                async with session.get('https://www.blackbox.ai/api/auth/session', cookies=get_cookies(cls.cookie_domain, False)) as resp:
                    resp.raise_for_status()
                    cls.session_data = await resp.json()

            # Check if we have a valid session
            if not cls.session_data:
                # No valid session found, raise an error
                debug.log("BlackboxPro: No valid session found in HAR files")
                raise NoValidHarFileError("No valid Blackbox session found. Please log in to Blackbox AI in your browser first.")

            debug.log(f"BlackboxPro: Using session from cookies / HAR file (email: {cls.session_data['user'].get('email', 'unknown')})")

            # Check subscription status
            subscription_status = {"status": "FREE", "customerId": None, "isTrialSubscription": False, "lastChecked": None}
            if cls.session_data.get('user', {}).get('email'):
                subscription_status = await cls.check_subscription(cls.session_data['user']['email'])
                debug.log(f"BlackboxPro: Subscription status for {cls.session_data['user']['email']}: {subscription_status['status']}")

            # Determine if user has premium access based on subscription status
            is_premium = False
            if subscription_status['status'] == "PREMIUM":
                is_premium = True
            else:
                # For free accounts, check for requested model
                if model:
                    debug.log(f"BlackboxPro: Model {model} not available in free account, falling back to default model")
                    model = cls.default_model

            data = {
                "messages": current_messages,
                "id": conversation.chat_id,
                "previewToken": None,
                "userId": None,
                "codeModelMode": True,
                "trendingAgentMode": {},
                "isMicMode": False,
                "userSystemPrompt": None,
                "maxTokens": max_tokens,
                "playgroundTopP": top_p,
                "playgroundTemperature": temperature,
                "isChromeExt": False,
                "githubToken": "",
                "clickedAnswer2": False,
                "clickedAnswer3": False,
                "clickedForceWebSearch": False,
                "visitFromDelta": False,
                "isMemoryEnabled": False,
                "mobileClient": False,
                "userSelectedModel": model if model else None,
                "userSelectedAgent": "VscodeAgent",
                "validated": "a38f5889-8fef-46d4-8ede-bf4668b6a9bb",
                "imageGenerationMode": model == cls.default_image_model,
                "imageGenMode": "autoMode",
                "webSearchModePrompt": False,
                "deepSearchMode": False,
                "promptSelection": "",
                "domains": None,
                "vscodeClient": False,
                "codeInterpreterMode": False,
                "customProfile": {
                    "name": "",
                    "occupation": "",
                    "traits": [],
                    "additionalInfo": "",
                    "enableNewChats": False
                },
                "webSearchModeOption": {
                    "autoMode": True,
                    "webMode": False,
                    "offlineMode": False
                },
                "session": cls.session_data,
                "isPremium": is_premium, 
                "subscriptionCache": {
                    "status": subscription_status['status'],
                    "customerId": subscription_status['customerId'],
                    "isTrialSubscription": subscription_status['isTrialSubscription'],
                    "lastChecked": int(datetime.now().timestamp() * 1000)
                },
                "beastMode": False,
                "reasoningMode": False,
                "designerMode": False,
                "workspaceId": "",
                "asyncMode": False,
                "integrations": {},
                "isTaskPersistent": False,
                "selectedElement": None
            }

            # Continue with the API request and async generator behavior
            async with session.post(cls.api_endpoint, json=data, proxy=proxy) as response:
                await raise_for_status(response)

                # Collect the full response
                full_response = []
                async for chunk in response.content.iter_any():
                    if chunk:
                        chunk_text = chunk.decode()
                        if "You have reached your request limit for the hour" in chunk_text:
                            raise RateLimitError(chunk_text)
                        full_response.append(chunk_text)
                        # Only yield chunks for non-image models
                        if model != cls.default_image_model:
                            yield chunk_text

                full_response_text = ''.join(full_response)

                # For image models, check for image markdown
                if model == cls.default_image_model:
                    image_url_match = re.search(r'!\[.*?\]\((.*?)\)', full_response_text)
                    if image_url_match:
                        image_url = image_url_match.group(1)
                        yield ImageResponse(urls=[image_url], alt=format_media_prompt(messages, prompt))
                        return

                # Handle conversation history once, in one place
                if return_conversation:
                    yield conversation
                # For image models that didn't produce an image, fall back to text response
                elif model == cls.default_image_model:
                    yield full_response_text