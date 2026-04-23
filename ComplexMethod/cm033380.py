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