async def wss_media(
        cls,
        _session,
        conversation: Conversation,
        headers: Dict[str, str],
        auth_result: AuthResult,
        timeout: Optional[int] = 20,
    ):
        seen_assets: Set[str] = set()
        async with AsyncSession(
            timeout=timeout,
            impersonate="chrome",
            headers=headers,
            cookies=auth_result.cookies
        ) as session:
            response = await session.get(
                "https://chatgpt.com/backend-api/celsius/ws/user",
                headers=headers,
            )
            response.raise_for_status()
            websocket_url = response.json().get("websocket_url")
            started = False
            wss = await session.ws_connect(websocket_url, timeout=3)
            while not wss.closed:
                try:
                    last_msg = await wss.recv_json(timeout=60 if not started else timeout)
                except Exception:
                    break
                conversation_id = conversation.task.get("conversation_id")
                message_id = conversation.task.get("message", {}).get("id")
                if isinstance(last_msg, dict) and last_msg.get("type") == "conversation-update":
                    if last_msg.get("payload", {}).get("conversation_id") != conversation_id:
                        continue

                    message = last_msg.get("payload", {}).get("update_content", {}).get("message", {})
                    if message.get("id") != message_id:
                        continue

                    # if last_msg.get("payload", {}).get("update_type") == 'async-task-start':
                    #     started = True
                    started = True
                    if last_msg.get("payload", {}).get("update_type") == 'async-task-update-message':

                        status = message.get("status")
                        parts = message.get("content").get("parts") or []
                        for part in parts:
                            if part.get("content_type") != "image_asset_pointer":
                                continue
                            asset = part.get("asset_pointer")
                            if not asset or asset in seen_assets:
                                continue
                            seen_assets.add(asset)
                            generated_images = await cls.get_generated_image(
                                _session,
                                auth_result,
                                asset,
                                conversation.prompt or "",
                                conversation.conversation_id,
                                status,
                            )
                            if generated_images is not None:
                                yield generated_images
                        if message.get("status") == "finished_successfully":
                            await wss.close()
                            return