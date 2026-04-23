def _consolidate_calls(items: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Generator that walks through *items* and, whenever it meets the pair.

        {"type": "server_tool_call", "name": "web_search", "id": X, ...}
        {"type": "server_tool_result", "id": X}

    merges them into

        {"id": X,
         "output": ...,
         "status": ...,
         "type": "web_search_call"}

    keeping every other element untouched.
    """
    items = iter(items)  # make sure we have a true iterator
    for current in items:
        # Only a call can start a pair worth collapsing
        if current.get("type") != "server_tool_call":
            yield current
            continue

        try:
            nxt = next(items)  # look-ahead one element
        except StopIteration:  # no “result” - just yield the call back
            yield current
            break

        # If this really is the matching “result” - collapse
        if nxt.get("type") == "server_tool_result" and nxt.get(
            "tool_call_id"
        ) == current.get("id"):
            if current.get("name") == "web_search":
                collapsed = {"id": current["id"]}
                if "args" in current:
                    # N.B. as of 2025-09-17 OpenAI raises BadRequestError if sources
                    # are passed back in
                    collapsed["action"] = current["args"]

                if status := nxt.get("status"):
                    if status == "success":
                        collapsed["status"] = "completed"
                    elif status == "error":
                        collapsed["status"] = "failed"
                elif nxt.get("extras", {}).get("status"):
                    collapsed["status"] = nxt["extras"]["status"]
                else:
                    pass
                collapsed["type"] = "web_search_call"

            if current.get("name") == "file_search":
                collapsed = {"id": current["id"]}
                if "args" in current and "queries" in current["args"]:
                    collapsed["queries"] = current["args"]["queries"]

                if "output" in nxt:
                    collapsed["results"] = nxt["output"]
                if status := nxt.get("status"):
                    if status == "success":
                        collapsed["status"] = "completed"
                    elif status == "error":
                        collapsed["status"] = "failed"
                elif nxt.get("extras", {}).get("status"):
                    collapsed["status"] = nxt["extras"]["status"]
                else:
                    pass
                collapsed["type"] = "file_search_call"

            elif current.get("name") == "code_interpreter":
                collapsed = {"id": current["id"]}
                if "args" in current and "code" in current["args"]:
                    collapsed["code"] = current["args"]["code"]
                for key in ("container_id",):
                    if key in current:
                        collapsed[key] = current[key]
                    elif key in current.get("extras", {}):
                        collapsed[key] = current["extras"][key]
                    else:
                        pass

                if "output" in nxt:
                    collapsed["outputs"] = nxt["output"]
                if status := nxt.get("status"):
                    if status == "success":
                        collapsed["status"] = "completed"
                    elif status == "error":
                        collapsed["status"] = "failed"
                elif nxt.get("extras", {}).get("status"):
                    collapsed["status"] = nxt["extras"]["status"]
                collapsed["type"] = "code_interpreter_call"

            elif current.get("name") == "remote_mcp":
                collapsed = {"id": current["id"]}
                if "args" in current:
                    collapsed["arguments"] = json.dumps(
                        current["args"], separators=(",", ":")
                    )
                elif "arguments" in current.get("extras", {}):
                    collapsed["arguments"] = current["extras"]["arguments"]
                else:
                    pass

                if tool_name := current.get("extras", {}).get("tool_name"):
                    collapsed["name"] = tool_name
                if server_label := current.get("extras", {}).get("server_label"):
                    collapsed["server_label"] = server_label
                collapsed["type"] = "mcp_call"

                if approval_id := current.get("extras", {}).get("approval_request_id"):
                    collapsed["approval_request_id"] = approval_id
                if error := nxt.get("extras", {}).get("error"):
                    collapsed["error"] = error
                if "output" in nxt:
                    collapsed["output"] = nxt["output"]
                for k, v in current.get("extras", {}).items():
                    if k not in ("server_label", "arguments", "tool_name", "error"):
                        collapsed[k] = v

            elif current.get("name") == "mcp_list_tools":
                collapsed = {"id": current["id"]}
                if server_label := current.get("extras", {}).get("server_label"):
                    collapsed["server_label"] = server_label
                if "output" in nxt:
                    collapsed["tools"] = nxt["output"]
                collapsed["type"] = "mcp_list_tools"
                if error := nxt.get("extras", {}).get("error"):
                    collapsed["error"] = error
                for k, v in current.get("extras", {}).items():
                    if k not in ("server_label", "error"):
                        collapsed[k] = v
            else:
                pass

            yield collapsed

        else:
            # Not a matching pair - emit both, in original order
            yield current
            yield nxt