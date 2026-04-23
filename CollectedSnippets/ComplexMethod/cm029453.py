def summarize_responses_input_item(index: int, item: Any) -> str:
    item_dict = as_dict(item)
    if item_dict is None:
        return f"{index:02d} item_type={type(item).__name__}"

    if "role" in item_dict:
        role = ensure_str(item_dict.get("role", "unknown"))
        content = item_dict.get("content", "")
        if isinstance(content, str):
            return (
                f"{index:02d} role={role} content=str chars={len(content)} "
                f"preview='{truncate_for_log(content)}'"
            )
        if isinstance(content, list):
            part_summaries = [summarize_content_part(part) for part in content]
            return (
                f"{index:02d} role={role} content_parts={len(content)} "
                f"[{'; '.join(part_summaries)}]"
            )
        return f"{index:02d} role={role} content_type={type(content).__name__}"

    item_type = ensure_str(item_dict.get("type", "unknown"))

    if item_type in ("function_call", "custom_tool_call"):
        raw_args = (
            item_dict.get("input")
            if item_type == "custom_tool_call"
            else item_dict.get("arguments")
        )
        args_text = ensure_str(raw_args or "")
        call_id = item_dict.get("call_id") or item_dict.get("id")
        return (
            f"{index:02d} type={item_type} name={item_dict.get('name')} "
            f"call_id={call_id} args_chars={len(args_text)} "
            f"preview='{truncate_for_log(args_text)}'"
        )

    if item_type == "function_call_output":
        output_text = ensure_str(item_dict.get("output", ""))
        return (
            f"{index:02d} type=function_call_output call_id={item_dict.get('call_id')} "
            f"{summarize_function_call_output_payload(output_text)}"
        )

    if item_type == "message":
        role = ensure_str(item_dict.get("role", "unknown"))
        content = item_dict.get("content", [])
        if isinstance(content, list):
            part_summaries = [summarize_content_part(part) for part in content]
            return (
                f"{index:02d} type=message role={role} parts={len(content)} "
                f"[{'; '.join(part_summaries)}]"
            )
        return (
            f"{index:02d} type=message role={role} "
            f"content_type={type(content).__name__}"
        )

    if item_type == "reasoning":
        summary = item_dict.get("summary")
        if isinstance(summary, list):
            summary_parts = [summarize_content_part(part) for part in summary]
            return (
                f"{index:02d} type=reasoning summary_parts={len(summary)} "
                f"[{'; '.join(summary_parts)}]"
            )
        return f"{index:02d} type=reasoning summary_type={type(summary).__name__}"

    return f"{index:02d} type={item_type} keys={sorted(item_dict.keys())}"