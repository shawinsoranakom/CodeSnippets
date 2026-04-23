async def wait_media(
        cls,
        session,
        conversation,
        headers: Dict[str, str],
        auth_result: AuthResult,
        poll_interval: int = 10,
        timeout: Optional[int] = None,
    ) -> AsyncGenerator[Any, None]:
        start_time = asyncio.get_event_loop().time()
        seen_assets: Set[str] = set()
        running = True
        has_image_task = False
        generation_started = False

        while running:
            if timeout is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    return
            # https://chatgpt.com/backend-api/tasks
            async with session.get(
                    f"https://chatgpt.com/backend-api/conversation/{conversation.conversation_id}",
                    headers=headers,
            ) as response:
                await raise_for_status(response)
                data = await response.json()

            mapping = data.get("mapping") or {}
            if not mapping:
                return

            last_node = list(mapping.values())[-1] or {}
            last_message = last_node.get("message") or {}
            metadata = last_message.get("metadata") or {}
            status = last_message.get("status")
            image_task_id = metadata.get("image_gen_task_id")
            if not has_image_task and not image_task_id:
                return

            if image_task_id and not has_image_task:
                debug.log(f"OpenaiChat: Wait Task: {image_task_id}")
                has_image_task = True
            if status == "in_progress":
                generation_started = True
            elif generation_started and status == "finished_successfully":
                running = False
            if generation_started:
                content = last_message.get("content") or {}
                parts = content.get("parts") or []
                for part in parts:
                    if part.get("content_type") != "image_asset_pointer":
                        continue
                    asset = part.get("asset_pointer")
                    if not asset or asset in seen_assets:
                        continue
                    seen_assets.add(asset)
                    generated_images = await cls.get_generated_image(
                        session,
                        auth_result,
                        asset,
                        conversation.prompt
                        or metadata.get("async_task_title")
                        or "",
                        conversation.conversation_id,
                        status,
                    )
                    if generated_images is not None:
                        yield generated_images
            if generation_started and status == "finished_successfully":
                return
            await asyncio.sleep(poll_interval)