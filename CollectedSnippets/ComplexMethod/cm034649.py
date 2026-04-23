async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        api_key: str = None,
        **kwargs,
    ) -> AsyncResult:
        if not has_cloudscraper:
            raise MissingRequirementsError(
                "cloudscraper library is required for Yupp provider | install it via 'pip install cloudscraper'"
            )
        if not api_key:
            api_key = AuthManager.load_api_key(cls)
        if not api_key:
            api_key = get_cookie_tokens()
        if api_key:
            load_yupp_accounts(api_key)
            log_debug(f"Yupp provider initialized with {len(YUPP_ACCOUNTS)} accounts")
        else:
            raise MissingAuthError(
                "No Yupp accounts configured. Set YUPP_API_KEY environment variable."
            )

        conversation = kwargs.get("conversation")
        url_uuid = conversation.url_uuid if conversation else None
        is_new_conversation = url_uuid is None

        prompt = kwargs.get("prompt")
        if prompt is None:
            if is_new_conversation:
                prompt = format_messages_for_yupp(messages)
            else:
                prompt = get_last_user_message(messages, prompt)

        log_debug(
            f"Use url_uuid: {url_uuid}, Formatted prompt length: {len(prompt)}, Is new conversation: {is_new_conversation}"
        )

        max_attempts = len(YUPP_ACCOUNTS)
        for attempt in range(max_attempts):
            account = await get_best_yupp_account()
            if not account:
                raise ProviderException("No valid Yupp accounts available")

            try:
                scraper = create_scraper()
                if proxy:
                    scraper.proxies = {"http": proxy, "https": proxy}

                credits = await get_credits(scraper, account)
                log_debug(f"Account ...{account['token'][-4:]} has {credits} credits")
                if credits is not None and credits <= 100:
                    log_debug(f"Account ...{account['token'][-4:]} has low credits, rotating")
                    async with account_rotation_lock:
                        account["error_count"] += 1
                    continue

                # Initialize token extractor for automatic token swapping
                token_extractor = get_token_extractor(
                    jwt_token=account["token"], scraper=scraper
                )

                turn_id = str(uuid.uuid4())

                media = kwargs.get("media")
                if media:
                    media_ = list(merge_media(media, messages))
                    files = await cls.prepare_files(
                        media_, scraper=scraper, account=account
                    )
                else:
                    files = []

                mode = "image" if model in cls.image_models else "text"

                if is_new_conversation:
                    url_uuid = str(uuid.uuid4())
                    payload = [
                        url_uuid,
                        turn_id,
                        prompt,
                        "$undefined",
                        "$undefined",
                        files,
                        "$undefined",
                        [{"modelName": model, "promptModifierId": "$undefined"}]
                        if model
                        else "none",
                        mode,
                        True,
                        "$undefined",
                    ]
                    url = f"https://yupp.ai/chat/{url_uuid}?stream=true"
                    yield JsonConversation(url_uuid=url_uuid)
                    next_action = kwargs.get(
                        "next_action",
                        await token_extractor.get_token("new_conversation"),
                    )
                else:
                    payload = [
                        url_uuid,
                        turn_id,
                        prompt,
                        False,
                        [],
                        [{"modelName": model, "promptModifierId": "$undefined"}]
                        if model
                        else [],
                        mode,
                        files,
                    ]
                    url = f"https://yupp.ai/chat/{url_uuid}?stream=true"
                    next_action = kwargs.get(
                        "next_action",
                        await token_extractor.get_token("existing_conversation"),
                    )

                headers = {
                    "accept": "text/x-component",
                    "content-type": "text/plain;charset=UTF-8",
                    "next-action": next_action,
                    "cookie": f"__Secure-yupp.session-token={account['token']}",
                }

                log_debug(f"Sending request to: {url}")
                log_debug(
                    f"Payload structure: {type(payload)}, length: {len(str(payload))}"
                )

                _timeout = kwargs.get("timeout")
                if isinstance(_timeout, (int, float)):
                    timeout = int(_timeout)
                else:
                    timeout = 5 * 60

                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    _executor,
                    cls.sync_stream_request,
                    scraper,
                    url,
                    payload,
                    headers,
                    timeout,
                )

                try:
                    async for chunk in cls._process_stream_response(
                        response, account, scraper, prompt, model
                    ):
                        yield chunk
                finally:
                    response.close()
                    if not kwargs.get("conversation"):
                        asyncio.create_task(delete_chat(scraper, account, url_uuid))
                return

            except RateLimitError:
                log_debug(
                    f"Account ...{account['token'][-4:]} hit rate limit, rotating"
                )
                async with account_rotation_lock:
                    account["error_count"] += 1
                continue

            except ProviderException as e:
                log_debug(f"Account ...{account['token'][-4:]} failed: {str(e)}")
                error_msg = str(e).lower()

                # Check if this is a token-related error
                if any(
                    x in error_msg
                    for x in [
                        "auth",
                        "401",
                        "403",
                        "404",
                        "invalid action",
                        "action",
                        "next-action",
                    ]
                ):
                    # Mark token as failed to trigger extraction
                    token_type = (
                        "new_conversation"
                        if is_new_conversation
                        else "existing_conversation"
                    )
                    await token_extractor.mark_token_failed(token_type, next_action)
                    log_debug(
                        f"Token failure detected, marked for extraction: {token_type}"
                    )

                async with account_rotation_lock:
                    if "auth" in error_msg or "401" in error_msg or "403" in error_msg:
                        account["is_valid"] = False
                    else:
                        account["error_count"] += 1
                continue

            except Exception as e:
                log_debug(
                    f"Unexpected error with account ...{account['token'][-4:]}: {str(e)}"
                )
                error_str = str(e).lower()

                # Check for token-related errors in generic exceptions too
                if any(x in error_str for x in ["404", "401", "403", "invalid action"]):
                    token_type = (
                        "new_conversation"
                        if is_new_conversation
                        else "existing_conversation"
                    )
                    await token_extractor.mark_token_failed(token_type, next_action)
                    log_debug(
                        f"Token failure detected in exception handler: {token_type}"
                    )

                if "500" in error_str or "internal server error" in error_str:
                    async with account_rotation_lock:
                        account["error_count"] += 1
                    continue
                async with account_rotation_lock:
                    account["error_count"] += 1
                raise ProviderException(f"Yupp request failed: {str(e)}") from e

        raise ProviderException("All Yupp accounts failed after rotation attempts")