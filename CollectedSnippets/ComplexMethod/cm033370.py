async def chat_completion_openai_like(tenant_id, chat_id):
    """
    OpenAI-like chat completion API that simulates the behavior of OpenAI's completions endpoint.

    This function allows users to interact with a model and receive responses based on a series of historical messages.
    If `stream` is set to True (by default), the response will be streamed in chunks, mimicking the OpenAI-style API.
    Set `stream` to False explicitly, the response will be returned in a single complete answer.

    Reference:

    - If `stream` is True, the final answer and reference information will appear in the **last chunk** of the stream.
    - If `stream` is False, the reference will be included in `choices[0].message.reference`.
    - If `extra_body.reference_metadata.include` is True, each reference chunk may include `document_metadata` in both streaming and non-streaming responses.

    Example usage:

    curl -X POST https://ragflow_address.com/api/v1/chats_openai/<chat_id>/chat/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $RAGFLOW_API_KEY" \
        -d '{
            "model": "model",
            "messages": [{"role": "user", "content": "Say this is a test!"}],
            "stream": true
        }'

    Alternatively, you can use Python's `OpenAI` client:

    NOTE: Streaming via `client.chat.completions.create(stream=True, ...)` does
    not return `reference` currently. The only way to return `reference` is
    non-stream mode with `with_raw_response`.

    from openai import OpenAI
    import json

    model = "model"
    client = OpenAI(api_key="ragflow-api-key", base_url=f"http://ragflow_address/api/v1/chats_openai/<chat_id>")

    stream = True
    reference = True

    request_kwargs = dict(
        model="model",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who are you?"},
            {"role": "assistant", "content": "I am an AI assistant named..."},
            {"role": "user", "content": "Can you tell me how to install neovim"},
        ],
        extra_body={
            "reference": reference,
            "reference_metadata": {
                "include": True,
                "fields": ["author", "year", "source"],
            },
            "metadata_condition": {
                "logic": "and",
                "conditions": [
                    {
                        "name": "author",
                        "comparison_operator": "is",
                        "value": "bob"
                    }
                ]
            }
        },
    )

    if stream:
        completion = client.chat.completions.create(stream=True, **request_kwargs)
        for chunk in completion:
            print(chunk)
    else:
        resp = client.chat.completions.with_raw_response.create(
            stream=False, **request_kwargs
        )
        print("status:", resp.http_response.status_code)
        raw_text = resp.http_response.text
        print("raw:", raw_text)

        data = json.loads(raw_text)
        print("assistant:", data["choices"][0]["message"].get("content"))
        print("reference:", data["choices"][0]["message"].get("reference"))

    """
    req = await get_request_json()

    extra_body = req.get("extra_body") or {}
    if extra_body and not isinstance(extra_body, dict):
        return get_error_data_result("extra_body must be an object.")

    need_reference = bool(extra_body.get("reference", False))
    reference_metadata = extra_body.get("reference_metadata") or {}
    if reference_metadata and not isinstance(reference_metadata, dict):
        return get_error_data_result("reference_metadata must be an object.")
    include_reference_metadata = bool(reference_metadata.get("include", False))
    metadata_fields = reference_metadata.get("fields")
    if metadata_fields is not None and not isinstance(metadata_fields, list):
        return get_error_data_result("reference_metadata.fields must be an array.")

    messages = req.get("messages", [])
    # To prevent empty [] input
    if len(messages) < 1:
        return get_error_data_result("You have to provide messages.")
    if messages[-1]["role"] != "user":
        return get_error_data_result("The last content of this conversation is not from user.")

    prompt = messages[-1]["content"]
    # Treat context tokens as reasoning tokens
    context_token_used = sum(num_tokens_from_string(message["content"]) for message in messages)

    dia = DialogService.query(tenant_id=tenant_id, id=chat_id, status=StatusEnum.VALID.value)
    if not dia:
        return get_error_data_result(f"You don't own the chat {chat_id}")
    dia = dia[0]

    metadata_condition = extra_body.get("metadata_condition") or {}
    if metadata_condition and not isinstance(metadata_condition, dict):
        return get_error_data_result(message="metadata_condition must be an object.")

    doc_ids_str = None
    if metadata_condition:
        metas = DocMetadataService.get_flatted_meta_by_kbs(dia.kb_ids or [])
        filtered_doc_ids = meta_filter(
            metas,
            convert_conditions(metadata_condition),
            metadata_condition.get("logic", "and"),
        )
        if metadata_condition.get("conditions") and not filtered_doc_ids:
            filtered_doc_ids = ["-999"]
        doc_ids_str = ",".join(filtered_doc_ids) if filtered_doc_ids else None

    # Filter system and non-sense assistant messages
    msg = []
    for m in messages:
        if m["role"] == "system":
            continue
        if m["role"] == "assistant" and not msg:
            continue
        msg.append(m)

    # tools = get_tools()
    # toolcall_session = SimpleFunctionCallServer()
    tools = None
    toolcall_session = None

    if req.get("stream", True):
        # The value for the usage field on all chunks except for the last one will be null.
        # The usage field on the last chunk contains token usage statistics for the entire request.
        # The choices field on the last chunk will always be an empty array [].
        async def streamed_response_generator(chat_id, dia, msg):
            token_used = 0
            last_ans = {}
            full_content = ""
            full_reasoning = ""
            final_answer = None
            final_reference = None
            in_think = False
            response = {
                "id": f"chatcmpl-{chat_id}",
                "choices": [
                    {
                        "delta": {
                            "content": "",
                            "role": "assistant",
                            "function_call": None,
                            "tool_calls": None,
                            "reasoning_content": "",
                        },
                        "finish_reason": None,
                        "index": 0,
                        "logprobs": None,
                    }
                ],
                "created": int(time.time()),
                "model": "model",
                "object": "chat.completion.chunk",
                "system_fingerprint": "",
                "usage": None,
            }

            try:
                chat_kwargs = {"toolcall_session": toolcall_session, "tools": tools, "quote": need_reference}
                if doc_ids_str:
                    chat_kwargs["doc_ids"] = doc_ids_str
                async for ans in async_chat(dia, msg, True, **chat_kwargs):
                    last_ans = ans
                    if ans.get("final"):
                        if ans.get("answer"):
                            full_content = ans["answer"]
                            response["choices"][0]["delta"]["content"] = full_content
                            response["choices"][0]["delta"]["reasoning_content"] = None
                            yield f"data:{json.dumps(response, ensure_ascii=False)}\n\n"
                        final_answer = full_content
                        final_reference = ans.get("reference", {})
                        continue
                    if ans.get("start_to_think"):
                        in_think = True
                        continue
                    if ans.get("end_to_think"):
                        in_think = False
                        continue
                    delta = ans.get("answer") or ""
                    if not delta:
                        continue
                    token_used += num_tokens_from_string(delta)
                    if in_think:
                        full_reasoning += delta
                        response["choices"][0]["delta"]["reasoning_content"] = delta
                        response["choices"][0]["delta"]["content"] = None
                    else:
                        full_content += delta
                        response["choices"][0]["delta"]["content"] = delta
                        response["choices"][0]["delta"]["reasoning_content"] = None
                    yield f"data:{json.dumps(response, ensure_ascii=False)}\n\n"
            except Exception as e:
                response["choices"][0]["delta"]["content"] = "**ERROR**: " + str(e)
                yield f"data:{json.dumps(response, ensure_ascii=False)}\n\n"

            # The last chunk
            response["choices"][0]["delta"]["content"] = None
            response["choices"][0]["delta"]["reasoning_content"] = None
            response["choices"][0]["finish_reason"] = "stop"
            prompt_tokens = num_tokens_from_string(prompt)
            response["usage"] = {"prompt_tokens": prompt_tokens, "completion_tokens": token_used, "total_tokens": prompt_tokens + token_used}
            if need_reference:
                reference_payload = final_reference if final_reference is not None else last_ans.get("reference", [])
                response["choices"][0]["delta"]["reference"] = _build_reference_chunks(
                    reference_payload,
                    include_metadata=include_reference_metadata,
                    metadata_fields=metadata_fields,
                )
                response["choices"][0]["delta"]["final_content"] = final_answer if final_answer is not None else full_content
            yield f"data:{json.dumps(response, ensure_ascii=False)}\n\n"
            yield "data:[DONE]\n\n"

        resp = Response(streamed_response_generator(chat_id, dia, msg), mimetype="text/event-stream")
        resp.headers.add_header("Cache-control", "no-cache")
        resp.headers.add_header("Connection", "keep-alive")
        resp.headers.add_header("X-Accel-Buffering", "no")
        resp.headers.add_header("Content-Type", "text/event-stream; charset=utf-8")
        return resp
    else:
        answer = None
        chat_kwargs = {"toolcall_session": toolcall_session, "tools": tools, "quote": need_reference}
        if doc_ids_str:
            chat_kwargs["doc_ids"] = doc_ids_str
        async for ans in async_chat(dia, msg, False, **chat_kwargs):
            # focus answer content only
            answer = ans
            break
        content = answer["answer"]

        response = {
            "id": f"chatcmpl-{chat_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.get("model", ""),
            "usage": {
                "prompt_tokens": num_tokens_from_string(prompt),
                "completion_tokens": num_tokens_from_string(content),
                "total_tokens": num_tokens_from_string(prompt) + num_tokens_from_string(content),
                "completion_tokens_details": {
                    "reasoning_tokens": context_token_used,
                    "accepted_prediction_tokens": num_tokens_from_string(content),
                    "rejected_prediction_tokens": 0,  # 0 for simplicity
                },
            },
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "logprobs": None,
                    "finish_reason": "stop",
                    "index": 0,
                }
            ],
        }
        if need_reference:
            response["choices"][0]["message"]["reference"] = _build_reference_chunks(
                answer.get("reference", {}),
                include_metadata=include_reference_metadata,
                metadata_fields=metadata_fields,
            )

        return jsonify(response)