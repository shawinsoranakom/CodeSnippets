async def completion_openai(tenant_id, agent_id, question, session_id=None, stream=True, **kwargs):
    tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
    prompt_tokens = len(tiktoken_encoder.encode(str(question)))
    user_id = kwargs.get("user_id", "")

    if stream:
        completion_tokens = 0
        try:
            async for ans in completion(
                tenant_id=tenant_id,
                agent_id=agent_id,
                session_id=session_id,
                query=question,
                user_id=user_id,
                **kwargs
            ):
                if isinstance(ans, str):
                    try:
                        ans = json.loads(ans[5:])  # remove "data:"
                    except Exception as e:
                        logging.exception(f"Agent OpenAI-Compatible completion_openai parse answer failed: {e}")
                        continue
                if ans.get("event") not in ["message", "message_end"]:
                    continue

                content_piece = ""
                if ans["event"] == "message":
                    content_piece = ans["data"]["content"]

                completion_tokens += len(tiktoken_encoder.encode(content_piece))

                openai_data = get_data_openai(
                        id=session_id or str(uuid4()),
                        model=agent_id,
                        content=content_piece,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        stream=True
                    )

                if ans.get("data", {}).get("reference", None):
                    openai_data["choices"][0]["delta"]["reference"] = ans["data"]["reference"]

                yield "data: " + json.dumps(openai_data, ensure_ascii=False) + "\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logging.exception(e)
            yield "data: " + json.dumps(
                get_data_openai(
                    id=session_id or str(uuid4()),
                    model=agent_id,
                    content=f"**ERROR**: {str(e)}",
                    finish_reason="stop",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=len(tiktoken_encoder.encode(f"**ERROR**: {str(e)}")),
                    stream=True
                ),
                ensure_ascii=False
            ) + "\n\n"
            yield "data: [DONE]\n\n"

    else:
        try:
            all_content = ""
            reference = {}
            async for ans in completion(
                tenant_id=tenant_id,
                agent_id=agent_id,
                session_id=session_id,
                query=question,
                user_id=user_id,
                **kwargs
            ):
                if isinstance(ans, str):
                    ans = json.loads(ans[5:])
                if ans.get("event") not in ["message", "message_end"]:
                    continue

                if ans["event"] == "message":
                    all_content += ans["data"]["content"]

                if ans.get("data", {}).get("reference", None):
                    reference.update(ans["data"]["reference"])

            completion_tokens = len(tiktoken_encoder.encode(all_content))

            openai_data = get_data_openai(
                id=session_id or str(uuid4()),
                model=agent_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                content=all_content,
                finish_reason="stop",
                param=None
            )

            if reference:
                openai_data["choices"][0]["message"]["reference"] = reference

            yield openai_data
        except Exception as e:
            logging.exception(e)
            yield get_data_openai(
                id=session_id or str(uuid4()),
                model=agent_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=len(tiktoken_encoder.encode(f"**ERROR**: {str(e)}")),
                content=f"**ERROR**: {str(e)}",
                finish_reason="stop",
                param=None
            )