async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        cookies: Cookies = None,
        headers: dict = None,
        proxy: str = None,
        conversation: JsonConversation = None,
        web_search: bool = False,
        media: list = None,
        delete_session: bool = False,
        **kwargs
    ) -> AsyncResult:
        """
        Create async generator for DeepSeek requests with HAR file support.

        Authentication priority:
        1. HAR file cookies and auth token (har_and_cookies/deepseek*.har)
        2. Cookie jar from get_cookies()

        Note: DeepSeek requires proof-of-work challenge which may require
        additional handling. This implementation provides basic HAR-based auth.

        Args:
            model: Model name to use
            messages: Message history
            cookies: Optional cookies
            proxy: Optional proxy
            conversation: JsonConversation object for continuing sessions
            web_search: Enable web search
            media: List of (file_bytes, filename) tuples for file upload
        """
        if not model:
            model = cls.default_model

        # Try to get auth from HAR file first
        if cookies is None:
            cookies = get_cookies(cls.cookie_domain, False)
            headers = get_headers(cls.cookie_domain)
            if cookies and headers.get("authorization"):
                debug.log(f"DeepSeekAuth: Using {len(cookies)} cookies and {len(headers)} headers from cookie jar")
            else:
                raise MissingAuthError(
                    "DeepSeekAuth: No authentication found. "
                    "Please add a DeepSeek HAR file to har_and_cookies/ directory "
                    "with an authorization token."
                )

        # Initialize conversation if needed
        if conversation is None:
            conversation = JsonConversation(
                parent_message_id=None
            )

        # Get auth token from HAR data or conversation
        authorization = None
        if headers:
            authorization = headers.get("authorization")
        elif hasattr(conversation, 'authorization'):
            authorization = conversation.authorization

        if not authorization:
            raise MissingAuthError(
                "DeepSeekAuth: Authorization token required. "
                "Please ensure HAR file contains authorization header."
            )

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": cls.url,
            "referer": f"{cls.url}/",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "x-app-version": "20241129.1",
            "x-client-locale": "en_US",
            "x-client-platform": "web",
            "x-client-timezone-offset": "-28800",
            "x-client-version": "1.7.0",
            "authorization": authorization,
        }

        # Extract query from messages
        prompt = get_last_user_message(messages)

        # Determine thinking mode
        thinking_enabled = bool(model) and "deepseek-r1" in model

        yield JsonRequest.from_dict({
            "prompt": prompt,
            "thinking_enabled": thinking_enabled,
            "search_enabled": web_search,
        })

        # Get proof-of-work challenge (required by DeepSeek)
        debug.log(f"DeepSeekAuth: Requesting PoW challenge from {POW_CHALLENGE_ENDPOINT}")
        async with StreamSession(
            headers=headers, 
            cookies=cookies, 
            proxy=proxy, 
            impersonate="chrome"
        ) as session:
            async with session.post(
                POW_CHALLENGE_ENDPOINT,
                json={"target_path": "/api/v0/chat/completion"}
            ) as response:
                await raise_for_status(response)
                pow_data = await response.json()
                debug.log("DeepSeekAuth: PoW challenge received")

                # Extract challenge data
                if 'data' in pow_data and 'biz_data' in pow_data['data']:
                    challenge = pow_data['data']['biz_data']['challenge']
                    debug.log(f"DeepSeekAuth: Challenge: algorithm={challenge.get('algorithm')}, difficulty={challenge.get('difficulty')}")

                    # Use inline PoW solver to solve the challenge
                    pow_solver = DeepSeekPOW()
                    pow_response_str = pow_solver.solve_challenge(challenge)
                    debug.log(f"DeepSeekAuth: PoW challenge solved successfully")
                    headers["x-ds-pow-response"] = pow_response_str

        # Always create a new chat session for the first request
        if not hasattr(conversation, 'chat_session_id') or not conversation.chat_session_id:
            debug.log(f"DeepSeekAuth: Creating new chat session...")
            async with StreamSession(
                headers=headers, 
                cookies=cookies, 
                proxy=proxy, 
                impersonate="chrome"
            ) as session:
                async with session.post(CHAT_SESSION_CREATE_ENDPOINT) as response:
                    await raise_for_status(response)
                    session_data = await response.json()
                    # ID is nested in data.biz_data.id
                    if ('data' in session_data and 
                        'biz_data' in session_data['data'] and 
                        'id' in session_data['data']['biz_data']):
                        chat_session_id = session_data['data']['biz_data']['id']
                        conversation.chat_session_id = chat_session_id
                        debug.log(f"DeepSeekAuth: Chat session created: {chat_session_id}")
                    else:
                        debug.error(f"DeepSeekAuth: Unexpected session response: {session_data}")
                        raise Exception(f"Failed to parse session response: {session_data}")
        else:
            debug.log(f"DeepSeekAuth: Reusing existing chat session: {conversation.chat_session_id}")

        # Yield conversation object so caller can reuse it for subsequent messages
        yield conversation

        # Upload file if provided - use HTTP/1.1 to avoid HTTP/2 stream errors
        ref_file_ids = []
        if media is not None and len(media) > 0:
            # Take first file from media list
            file_bytes, filename = media[0]
            async with StreamSession(
                headers=headers, 
                cookies=cookies, 
                proxy=proxy, 
                impersonate="chrome",
                http_version=CurlHttpVersion.V1_1 if has_curl_cffi else None  # Force HTTP/1.1 to avoid HTTP/2 stream errors
            ) as session:
                upload_result = await cls.upload_file(session, file_bytes, filename)
                ref_file_ids.append(upload_result["file_id"])
                debug.log(f"DeepSeekAuth: Using file_id: {upload_result['file_id']}")

        # Build request data
        json_data = {
            "chat_session_id": getattr(conversation, 'chat_session_id', str(uuid.uuid4())),
            "prompt": prompt,
            "ref_file_ids": ref_file_ids,
            "thinking_enabled": thinking_enabled,
            "search_enabled": web_search,
            "client_stream_id": generate_client_stream_id(),
        }

        # Add parent_message_id if continuing conversation
        if hasattr(conversation, 'parent_message_id') and conversation.parent_message_id:
            json_data["parent_message_id"] = conversation.parent_message_id

        # debug.log(f"DeepSeekAuth: Sending request to {CHAT_COMPLETION_ENDPOINT}")

        async with StreamSession(
            headers=headers, 
            cookies=cookies, 
            proxy=proxy, 
            impersonate="chrome"
        ) as session:
            async with session.post(CHAT_COMPLETION_ENDPOINT, json=json_data) as response:
                # debug.log(f"DeepSeekAuth: Processing response... status={response.status}, content-type={response.headers.get('content-type', 'unknown')}")
                await raise_for_status(response)

                # Check if response is actually SSE or regular JSON
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' not in content_type.lower():
                    raise RuntimeError(f"Expected SSE response but got content-type: {content_type}")

                is_thinking = False
                async for stream_data in sse_stream(response):
                    # Handle different stream data formats
                    if isinstance(stream_data, dict):
                        # Handle first chunk with message IDs (for conversation continuity)
                        if 'response_message_id' in stream_data:
                            conversation.parent_message_id = stream_data['response_message_id']
                            # debug.log(f"DeepSeekAuth: Set parent_message_id to {conversation.parent_message_id}")

                        # Handle initial response with fragments (most common case)
                        # Format: {'v': {'response': {'fragments': [{'content': '42', ...}]}}}
                        if 'v' in stream_data and isinstance(stream_data['v'], dict):
                            response_obj = stream_data['v'].get('response', {})
                            fragments = response_obj.get('fragments', [])
                            for fragment in fragments:
                                if isinstance(fragment, dict) and 'content' in fragment:
                                    if fragment.get('type') == 'THINK':
                                        is_thinking = True
                                    content = fragment['content']
                                    if isinstance(content, str) and content:
                                        yield Reasoning(content) if is_thinking else content
                                        # debug.log(f"DeepSeekAuth: Initial fragment content: '{content}'")

                        # Handle APPEND operations that create new fragments with initial content
                        elif ('p' in stream_data and stream_data['p'] == 'response/fragments' and 
                            'o' in stream_data and stream_data['o'] == 'APPEND' and 
                            'v' in stream_data and isinstance(stream_data['v'], list)):

                            # Extract content from the new fragment
                            for fragment in stream_data['v']:
                                if isinstance(fragment, dict) and 'content' in fragment and isinstance(fragment['content'], str):
                                    is_thinking = False 
                                    yield fragment['content']
                                    # debug.log(f"DeepSeekAuth: APPEND fragment content: '{fragment['content']}'")

                        # Handle path-based updates (like 'response/fragments/-1/content')
                        elif 'p' in stream_data and 'v' in stream_data:
                            path = stream_data['p']
                            value = stream_data['v']

                            # Handle content updates
                            if path.endswith('/content') and isinstance(value, str):
                                yield Reasoning(value) if is_thinking else value
                                # debug.log(f"DeepSeekAuth: Content update: '{value}'")

                            # Handle status updates
                            elif path == 'response/status' and value == 'FINISHED':
                                # debug.log("DeepSeekAuth: Stream finished")
                                break

                        # Handle batch updates
                        elif 'o' in stream_data and stream_data['o'] == 'BATCH' and 'v' in stream_data:
                            for batch_item in stream_data['v']:
                                if isinstance(batch_item, dict) and 'p' in batch_item and 'v' in batch_item:
                                    if batch_item['p'] == 'response/status' and batch_item['v'] == 'FINISHED':
                                        # debug.log("DeepSeekAuth: Stream finished (batch)")
                                        break

                        # Handle shorthand content updates
                        elif 'v' in stream_data and isinstance(stream_data['v'], str):
                            yield Reasoning(stream_data['v']) if is_thinking else stream_data['v']
                            # debug.log(f"DeepSeekAuth: Shorthand content: '{stream_data['v']}'")


                # Ensure we yield the conversation object at the end
                yield conversation

                # Delete chat session only if explicitly requested (when conversation is fully done)
                if delete_session and hasattr(conversation, 'chat_session_id') and conversation.chat_session_id:
                    async with StreamSession(
                        headers=headers,
                        cookies=cookies,
                        proxy=proxy,
                        impersonate="chrome"
                    ) as delete_session_obj:
                        await cls.delete_chat_session(
                            delete_session_obj,
                            conversation.chat_session_id,
                            headers
                        )