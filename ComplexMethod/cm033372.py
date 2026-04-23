async def agent_completions(tenant_id, agent_id):
    req = await get_request_json()
    return_trace = bool(req.get("return_trace", False))

    if req.get("stream", True):

        async def generate():
            trace_items = []
            async for answer in agent_completion(tenant_id=tenant_id, agent_id=agent_id, **req):
                if isinstance(answer, str):
                    try:
                        ans = json.loads(answer[5:])  # remove "data:"
                    except Exception:
                        continue

                event = ans.get("event")
                if event == "node_finished":
                    if return_trace:
                        data = ans.get("data", {})
                        trace_items.append(
                            {
                                "component_id": data.get("component_id"),
                                "trace": [copy.deepcopy(data)],
                            }
                        )
                        ans.setdefault("data", {})["trace"] = trace_items
                        answer = "data:" + json.dumps(ans, ensure_ascii=False) + "\n\n"
                    yield answer

                if event not in ["message", "message_end"]:
                    continue

                yield answer

            yield "data:[DONE]\n\n"

        resp = Response(generate(), mimetype="text/event-stream")
        resp.headers.add_header("Cache-control", "no-cache")
        resp.headers.add_header("Connection", "keep-alive")
        resp.headers.add_header("X-Accel-Buffering", "no")
        resp.headers.add_header("Content-Type", "text/event-stream; charset=utf-8")
        return resp

    full_content = ""
    reference = {}
    final_ans = ""
    trace_items = []
    structured_output = {}
    async for answer in agent_completion(tenant_id=tenant_id, agent_id=agent_id, **req):
        try:
            ans = json.loads(answer[5:])

            if ans["event"] == "message":
                full_content += ans["data"]["content"]

            if ans.get("data", {}).get("reference", None):
                reference.update(ans["data"]["reference"])

            if ans.get("event") == "node_finished":
                data = ans.get("data", {})
                node_out = data.get("outputs", {})
                component_id = data.get("component_id")
                if component_id is not None and "structured" in node_out:
                    structured_output[component_id] = copy.deepcopy(node_out["structured"])
                if return_trace:
                    trace_items.append(
                        {
                            "component_id": data.get("component_id"),
                            "trace": [copy.deepcopy(data)],
                        }
                    )

            final_ans = ans
        except Exception as e:
            return get_result(data=f"**ERROR**: {str(e)}")
    final_ans["data"]["content"] = full_content
    final_ans["data"]["reference"] = reference
    if structured_output:
        final_ans["data"]["structured"] = structured_output
    if return_trace and final_ans:
        final_ans["data"]["trace"] = trace_items
    return get_result(data=final_ans)