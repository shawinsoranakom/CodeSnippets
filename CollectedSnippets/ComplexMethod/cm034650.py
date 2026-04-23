async def _process_stream_response(
        cls,
        response,
        account: Dict[str, Any],
        scraper: CloudScraper,
        prompt: str,
        model_id: str,
    ) -> AsyncResult:
        line_pattern = re.compile(b"^([0-9a-fA-F]+):(.*)")
        target_stream_id = None
        reward_info = None
        is_thinking = False
        thinking_content = ""
        normal_content = ""
        quick_content = ""
        variant_text = ""
        stream = {"target": [], "variant": [], "quick": [], "thinking": [], "extra": []}
        select_stream = [None, None]
        capturing_ref_id: Optional[str] = None
        capturing_lines: List[bytes] = []
        think_blocks: Dict[str, str] = {}
        image_blocks: Dict[str, str] = {}

        def extract_ref_id(ref):
            return (
                ref[2:]
                if ref and isinstance(ref, str) and ref.startswith("$@")
                else None
            )

        def extract_ref_name(ref: str) -> Optional[str]:
            if not isinstance(ref, str):
                return None
            if ref.startswith("$@"):
                return ref[2:]
            if ref.startswith("$") and len(ref) > 1:
                return ref[1:]
            return None

        def is_valid_content(content: str) -> bool:
            if not content or content in [None, "", "$undefined"]:
                return False
            return True

        async def process_content_chunk(
            content: str, chunk_id: str, line_count: int, *, for_target: bool = False
        ):
            nonlocal normal_content

            if not is_valid_content(content):
                return

            if '<yapp class="image-gen">' in content:
                img_block = (
                    content.split('<yapp class="image-gen">').pop().split("</yapp>")[0]
                )
                image_id = json.loads(img_block).get("image_id")
                signed_url = await cls.get_signed_image(scraper, image_id)
                img = ImageResponse(signed_url, prompt)
                yield img
                return

            if is_thinking:
                yield Reasoning(content)
            else:
                if for_target:
                    normal_content += content
                yield content

        def finalize_capture_block(ref_id: str, lines: List[bytes]):
            text = b"".join(lines).decode("utf-8", errors="ignore")

            think_start = text.find("<think>")
            think_end = text.find("</think>")
            if think_start != -1 and think_end != -1 and think_end > think_start:
                inner = text[think_start + len("<think>") : think_end].strip()
                if inner:
                    think_blocks[ref_id] = inner

            yapp_start = text.find('<yapp class="image-gen">')
            if yapp_start != -1:
                yapp_end = text.find("</yapp>", yapp_start)
                if yapp_end != -1:
                    yapp_block = text[yapp_start : yapp_end + len("</yapp>")]
                    image_blocks[ref_id] = yapp_block

        try:
            line_count = 0
            quick_response_id = None
            variant_stream_id = None
            is_started: bool = False
            variant_image: Optional[ImageResponse] = None
            reward_id = "a"
            reward_kw = {}
            routing_id = "e"
            turn_id = None
            persisted_turn_id = None
            left_message_id = None
            right_message_id = None
            nudge_new_chat_id = None
            nudge_new_chat = False

            loop = asyncio.get_event_loop()

            def iter_lines():
                for line in response.iter_lines():
                    if line:
                        yield line

            lines_iterator = iter_lines()

            while True:
                try:
                    line = await loop.run_in_executor(
                        _executor, lambda: next(lines_iterator, None)
                    )
                    if line is None:
                        break
                except StopIteration:
                    break

                line_count += 1

                if isinstance(line, str):
                    line = line.encode()

                if capturing_ref_id is not None:
                    capturing_lines.append(line)

                    if b"</yapp>" in line:
                        idx = line.find(b"</yapp>")
                        suffix = line[idx + len(b"</yapp>") :]
                        finalize_capture_block(capturing_ref_id, capturing_lines)
                        capturing_ref_id = None
                        capturing_lines = []

                        if suffix.strip():
                            line = suffix
                        else:
                            continue
                    else:
                        continue

                match = line_pattern.match(line)
                if not match:
                    if b"<think>" in line:
                        m = line_pattern.match(line)
                        if m:
                            capturing_ref_id = m.group(1).decode()
                            capturing_lines = [line]
                            continue
                    continue

                chunk_id, chunk_data = match.groups()
                chunk_id = chunk_id.decode()

                if nudge_new_chat_id and chunk_id == nudge_new_chat_id:
                    nudge_new_chat = chunk_data.decode()
                    continue

                try:
                    data = json.loads(chunk_data) if chunk_data != b"{}" else {}
                except json.JSONDecodeError:
                    continue

                if (
                    chunk_id == reward_id
                    and isinstance(data, dict)
                    and "unclaimedRewardInfo" in data
                ):
                    reward_info = data
                    log_debug(f"Found reward info")

                elif chunk_id == "1":
                    yield PlainTextResponse(line.decode(errors="ignore"))
                    if isinstance(data, dict):
                        left_stream = data.get("leftStream", {})
                        right_stream = data.get("rightStream", {})
                        if data.get("quickResponse", {}) != "$undefined":
                            quick_response_id = extract_ref_id(
                                data.get("quickResponse", {})
                                .get("stream", {})
                                .get("next")
                            )

                        if data.get("turnId", {}) != "$undefined":
                            turn_id = extract_ref_id(data.get("turnId", {}).get("next"))
                        if data.get("persistedTurn", {}) != "$undefined":
                            persisted_turn_id = extract_ref_id(
                                data.get("persistedTurn", {}).get("next")
                            )
                        if data.get("leftMessageId", {}) != "$undefined":
                            left_message_id = extract_ref_id(
                                data.get("leftMessageId", {}).get("next")
                            )
                        if data.get("rightMessageId", {}) != "$undefined":
                            right_message_id = extract_ref_id(
                                data.get("rightMessageId", {}).get("next")
                            )

                        reward_id = (
                            extract_ref_id(data.get("pendingRewardActionResult", ""))
                            or reward_id
                        )
                        routing_id = (
                            extract_ref_id(data.get("routingResultPromise", ""))
                            or routing_id
                        )
                        nudge_new_chat_id = (
                            extract_ref_id(data.get("nudgeNewChatPromise", ""))
                            or nudge_new_chat_id
                        )
                        select_stream = [left_stream, right_stream]

                elif chunk_id == routing_id:
                    yield PlainTextResponse(line.decode(errors="ignore"))
                    if isinstance(data, dict):
                        provider_info = cls.get_dict()
                        provider_info["model"] = model_id
                        for i, selection in enumerate(data.get("modelSelections", [])):
                            if selection.get("selectionSource") == "USER_SELECTED" or i == 0:
                                target_stream_id = extract_ref_id(
                                    select_stream[i].get("next")
                                )
                                reward_kw["selection"] = "left" if i == 0 else "right"
                                provider_info["modelLabel"] = selection.get(
                                    "shortLabel"
                                )
                                provider_info["modelUrl"] = selection.get("externalUrl")
                                log_debug(f"Found target stream ID: {target_stream_id}")
                            if selection.get("selectionSource") != "USER_SELECTED":
                                variant_stream_id = extract_ref_id(
                                    select_stream[i].get("next")
                                )
                                provider_info["variantLabel"] = selection.get(
                                    "shortLabel"
                                )
                                provider_info["variantUrl"] = selection.get(
                                    "externalUrl"
                                )
                                log_debug(
                                    f"Found variant stream ID: {variant_stream_id}"
                                )
                        yield ProviderInfo.from_dict(provider_info)

                elif target_stream_id and chunk_id == target_stream_id:
                    yield PlainTextResponse(line.decode(errors="ignore"))
                    if isinstance(data, dict):
                        target_stream_id = extract_ref_id(data.get("next"))
                        content = data.get("curr", "")
                        if content:
                            ref_name = extract_ref_name(content)
                            if ref_name and (
                                ref_name in think_blocks or ref_name in image_blocks
                            ):
                                if ref_name in think_blocks:
                                    t_text = think_blocks[ref_name]
                                    if t_text:
                                        reasoning = Reasoning(t_text)
                                        stream["thinking"].append(reasoning)

                                if ref_name in image_blocks:
                                    img_block_text = image_blocks[ref_name]
                                    async for chunk in process_content_chunk(
                                        img_block_text,
                                        ref_name,
                                        line_count,
                                        for_target=True,
                                    ):
                                        stream["target"].append(chunk)
                                        is_started = True
                                        yield chunk
                            else:
                                async for chunk in process_content_chunk(
                                    content, chunk_id, line_count, for_target=True
                                ):
                                    stream["target"].append(chunk)
                                    is_started = True
                                    yield chunk

                elif variant_stream_id and chunk_id == variant_stream_id:
                    yield PlainTextResponse("[Variant] " + line.decode(errors="ignore"))
                    if isinstance(data, dict):
                        variant_stream_id = extract_ref_id(data.get("next"))
                        content = data.get("curr", "")
                        if content:
                            async for chunk in process_content_chunk(
                                content, chunk_id, line_count, for_target=False
                            ):
                                stream["variant"].append(chunk)
                                if isinstance(chunk, ImageResponse):
                                    yield PreviewResponse(str(chunk))
                                else:
                                    variant_text += str(chunk)
                                    if not is_started:
                                        yield PreviewResponse(variant_text)

                elif quick_response_id and chunk_id == quick_response_id:
                    yield PlainTextResponse("[Quick] " + line.decode(errors="ignore"))
                    if isinstance(data, dict):
                        content = data.get("curr", "")
                        if content:
                            async for chunk in process_content_chunk(
                                content, chunk_id, line_count, for_target=False
                            ):
                                stream["quick"].append(chunk)
                            quick_content += content
                            yield PreviewResponse(content)

                elif chunk_id == turn_id:
                    reward_kw["turn_id"] = data.get("curr", "")

                elif chunk_id == persisted_turn_id:
                    pass

                elif chunk_id == right_message_id:
                    reward_kw["right_message_id"] = data.get("curr", "")

                elif chunk_id == left_message_id:
                    reward_kw["left_message_id"] = data.get("curr", "")

                elif isinstance(data, dict) and "curr" in data:
                    content = data.get("curr", "")
                    if content:
                        async for chunk in process_content_chunk(
                            content, chunk_id, line_count, for_target=False
                        ):
                            stream["extra"].append(chunk)
                            if (
                                isinstance(chunk, str)
                                and "<streaming stopped unexpectedly" in chunk
                            ):
                                yield FinishReason(chunk)

                        yield PlainTextResponse(
                            "[Extra] " + line.decode(errors="ignore")
                        )

            if variant_image is not None:
                yield variant_image
            elif variant_text:
                yield VariantResponse(variant_text)
            yield JsonResponse(**stream)
            log_debug(f"Finished processing {line_count} lines")

        finally:
            log_debug(f"Get Reward: {reward_kw}")
            if (
                reward_kw.get("turn_id")
                and reward_kw.get("left_message_id")
                and reward_kw.get("right_message_id")
            ):
                eval_id = await record_model_feedback(
                    scraper,
                    account,
                    reward_kw
                )
                if eval_id:
                    await claim_yupp_reward(scraper, account, eval_id)