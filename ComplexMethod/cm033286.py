def structure_answer(conv, ans, message_id, session_id):
    reference = ans["reference"]
    if not isinstance(reference, dict):
        reference = {}
        ans["reference"] = {}
    is_final = ans.get("final", True)

    chunk_list = chunks_format(reference)

    reference["chunks"] = chunk_list
    ans["id"] = message_id
    ans["session_id"] = session_id

    if not conv:
        return ans

    if not conv.message:
        conv.message = []
    content = ans["answer"]
    if ans.get("start_to_think"):
        content = "<think>"
    elif ans.get("end_to_think"):
        content = "</think>"

    if not conv.message or conv.message[-1].get("role", "") != "assistant":
        conv.message.append({"role": "assistant", "content": content, "created_at": time.time(), "id": message_id})
    else:
        if is_final:
            if ans.get("answer"):
                conv.message[-1] = {"role": "assistant", "content": ans["answer"], "created_at": time.time(), "id": message_id}
            else:
                conv.message[-1]["created_at"] = time.time()
                conv.message[-1]["id"] = message_id
        else:
            conv.message[-1]["content"] = (conv.message[-1].get("content") or "") + content
            conv.message[-1]["created_at"] = time.time()
            conv.message[-1]["id"] = message_id
    if conv.reference:
        should_update_reference = is_final or bool(reference.get("chunks")) or bool(reference.get("doc_aggs"))
        if should_update_reference:
            conv.reference[-1] = reference
    return ans