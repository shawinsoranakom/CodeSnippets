async def event_generator():
        full_text = ""
        input_tokens = 0
        output_tokens = 0
        # Per-tool-call state keyed by the Chat Completions `tool_calls[].index`
        # which stays stable across chunks for the same call. Values are:
        #   {output_index, item_id, call_id, name, arguments, opened}
        tool_call_state: dict[int, dict] = {}
        # Text message lives at output_index 0; tool calls claim 1, 2, ...
        next_output_index = 1

        def _snapshot_output() -> list[dict]:
            """Snapshot of all completed output items for response.completed."""
            items: list[dict] = [
                {
                    "type": "message",
                    "id": msg_id,
                    "status": "completed",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": full_text,
                            "annotations": [],
                        }
                    ],
                }
            ]
            for st in sorted(tool_call_state.values(), key = lambda s: s["output_index"]):
                items.append(
                    {
                        "type": "function_call",
                        "id": st["item_id"],
                        "status": "completed",
                        "call_id": st["call_id"],
                        "name": st["name"],
                        "arguments": st["arguments"],
                    }
                )
            return items

        # ── Preamble events ──
        yield f"event: response.created\ndata: {json.dumps({'type': 'response.created', 'response': {'id': resp_id, 'object': 'response', 'created_at': created_at, 'status': 'in_progress', 'model': payload.model, 'output': [], 'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}})}\n\n"

        # output_item.added (text message at output_index 0)
        output_item = {
            "type": "message",
            "id": msg_id,
            "status": "in_progress",
            "role": "assistant",
            "content": [],
        }
        yield f"event: response.output_item.added\ndata: {json.dumps({'type': 'response.output_item.added', 'output_index': 0, 'item': output_item})}\n\n"

        # content_part.added
        content_part = {"type": "output_text", "text": "", "annotations": []}
        yield f"event: response.content_part.added\ndata: {json.dumps({'type': 'response.content_part.added', 'item_id': msg_id, 'output_index': 0, 'content_index': 0, 'part': content_part})}\n\n"

        # ── Direct httpx lifecycle to llama-server ──
        # Full same-task open + close, identical pattern to
        # _openai_passthrough_stream and _anthropic_passthrough_stream:
        # no `async with`, explicit aclose of lines_iter BEFORE resp /
        # client so the innermost httpcore byte stream is finalised in
        # this task (not via Python's asyncgen GC in a sibling task).
        client = httpx.AsyncClient(timeout = 600)
        resp = None
        lines_iter = None
        try:
            req = client.build_request("POST", target_url, json = body)
            try:
                resp = await client.send(req, stream = True)
            except httpx.RequestError as e:
                logger.error("responses stream: upstream unreachable: %s", e)
                yield f"event: response.failed\ndata: {json.dumps({'type': 'response.failed', 'response': {'id': resp_id, 'object': 'response', 'created_at': created_at, 'status': 'failed', 'model': payload.model, 'output': [], 'error': {'code': 502, 'message': _friendly_error(e)}}})}\n\n"
                return

            if resp.status_code != 200:
                err_bytes = await resp.aread()
                err_text = err_bytes.decode("utf-8", errors = "replace")
                logger.error(
                    "responses stream upstream error: status=%s body=%s",
                    resp.status_code,
                    err_text[:500],
                )
                yield f"event: response.failed\ndata: {json.dumps({'type': 'response.failed', 'response': {'id': resp_id, 'object': 'response', 'created_at': created_at, 'status': 'failed', 'model': payload.model, 'output': [], 'error': {'code': resp.status_code, 'message': f'llama-server error: {err_text[:500]}'}}})}\n\n"
                return

            lines_iter = resp.aiter_lines()
            async for raw_line in lines_iter:
                if await request.is_disconnected():
                    break
                if not raw_line:
                    continue
                if not raw_line.startswith("data: "):
                    continue
                data_str = raw_line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = chunk_data.get("choices", [])
                if not choices:
                    usage = chunk_data.get("usage")
                    if usage:
                        input_tokens = usage.get("prompt_tokens", input_tokens)
                        output_tokens = usage.get("completion_tokens", output_tokens)
                    continue

                delta = choices[0].get("delta", {}) or {}
                content = delta.get("content")
                if content:
                    full_text += content
                    delta_event = {
                        "type": "response.output_text.delta",
                        "item_id": msg_id,
                        "output_index": 0,
                        "content_index": 0,
                        "delta": content,
                    }
                    yield f"event: response.output_text.delta\ndata: {json.dumps(delta_event)}\n\n"

                for tc in delta.get("tool_calls") or []:
                    idx = tc.get("index", 0)
                    st = tool_call_state.get(idx)
                    fn = tc.get("function") or {}
                    if st is None:
                        # First chunk for this tool call — allocate an
                        # output_index and emit output_item.added.
                        st = {
                            "output_index": next_output_index,
                            "item_id": f"fc_{uuid.uuid4().hex[:12]}",
                            "call_id": tc.get("id") or "",
                            "name": fn.get("name") or "",
                            "arguments": "",
                            "opened": False,
                        }
                        next_output_index += 1
                        tool_call_state[idx] = st
                    else:
                        # Later chunks sometimes carry the id/name only
                        # once; merge when present.
                        if tc.get("id") and not st["call_id"]:
                            st["call_id"] = tc["id"]
                        if fn.get("name") and not st["name"]:
                            st["name"] = fn["name"]

                    if not st["opened"] and st["call_id"] and st["name"]:
                        item_added = {
                            "type": "response.output_item.added",
                            "output_index": st["output_index"],
                            "item": {
                                "type": "function_call",
                                "id": st["item_id"],
                                "status": "in_progress",
                                "call_id": st["call_id"],
                                "name": st["name"],
                                "arguments": "",
                            },
                        }
                        yield f"event: response.output_item.added\ndata: {json.dumps(item_added)}\n\n"
                        st["opened"] = True

                    arg_delta = fn.get("arguments") or ""
                    if arg_delta and st["opened"]:
                        st["arguments"] += arg_delta
                        args_delta_event = {
                            "type": "response.function_call_arguments.delta",
                            "item_id": st["item_id"],
                            "output_index": st["output_index"],
                            "delta": arg_delta,
                        }
                        yield f"event: response.function_call_arguments.delta\ndata: {json.dumps(args_delta_event)}\n\n"
                    elif arg_delta:
                        # Buffer the args until we can open the item
                        # (id/name arrive in the same chunk as the first
                        # arg delta for some models — but if not, stash).
                        st["arguments"] += arg_delta

                usage = chunk_data.get("usage")
                if usage:
                    input_tokens = usage.get("prompt_tokens", input_tokens)
                    output_tokens = usage.get("completion_tokens", output_tokens)
        except Exception as e:
            logger.error("responses stream error: %s", e)
        finally:
            if lines_iter is not None:
                try:
                    await lines_iter.aclose()
                except Exception:
                    pass
            if resp is not None:
                try:
                    await resp.aclose()
                except Exception:
                    pass
            try:
                await client.aclose()
            except Exception:
                pass

        # ── Closing events for tool calls ──
        for st in sorted(tool_call_state.values(), key = lambda s: s["output_index"]):
            # If id/name never arrived (malformed upstream), synthesise so
            # the client still sees a coherent frame sequence.
            if not st["opened"]:
                if not st["call_id"]:
                    st["call_id"] = f"call_{uuid.uuid4().hex[:12]}"
                item_added = {
                    "type": "response.output_item.added",
                    "output_index": st["output_index"],
                    "item": {
                        "type": "function_call",
                        "id": st["item_id"],
                        "status": "in_progress",
                        "call_id": st["call_id"],
                        "name": st["name"],
                        "arguments": "",
                    },
                }
                yield f"event: response.output_item.added\ndata: {json.dumps(item_added)}\n\n"
                if st["arguments"]:
                    yield (
                        "event: response.function_call_arguments.delta\n"
                        "data: "
                        + json.dumps(
                            {
                                "type": "response.function_call_arguments.delta",
                                "item_id": st["item_id"],
                                "output_index": st["output_index"],
                                "delta": st["arguments"],
                            }
                        )
                        + "\n\n"
                    )
                st["opened"] = True

            args_done = {
                "type": "response.function_call_arguments.done",
                "item_id": st["item_id"],
                "output_index": st["output_index"],
                "name": st["name"],
                "arguments": st["arguments"],
            }
            yield f"event: response.function_call_arguments.done\ndata: {json.dumps(args_done)}\n\n"

            item_done = {
                "type": "response.output_item.done",
                "output_index": st["output_index"],
                "item": {
                    "type": "function_call",
                    "id": st["item_id"],
                    "status": "completed",
                    "call_id": st["call_id"],
                    "name": st["name"],
                    "arguments": st["arguments"],
                },
            }
            yield f"event: response.output_item.done\ndata: {json.dumps(item_done)}\n\n"

        # ── Closing events for text message ──
        yield f"event: response.output_text.done\ndata: {json.dumps({'type': 'response.output_text.done', 'item_id': msg_id, 'output_index': 0, 'content_index': 0, 'text': full_text})}\n\n"

        yield f"event: response.content_part.done\ndata: {json.dumps({'type': 'response.content_part.done', 'item_id': msg_id, 'output_index': 0, 'content_index': 0, 'part': {'type': 'output_text', 'text': full_text, 'annotations': []}})}\n\n"

        yield f"event: response.output_item.done\ndata: {json.dumps({'type': 'response.output_item.done', 'output_index': 0, 'item': {'type': 'message', 'id': msg_id, 'status': 'completed', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': full_text, 'annotations': []}]}})}\n\n"

        # response.completed
        total_tokens = input_tokens + output_tokens
        completed_response = {
            "type": "response.completed",
            "response": {
                "id": resp_id,
                "object": "response",
                "created_at": created_at,
                "status": "completed",
                "model": payload.model,
                "output": _snapshot_output(),
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
            },
        }
        yield f"event: response.completed\ndata: {json.dumps(completed_response)}\n\n"