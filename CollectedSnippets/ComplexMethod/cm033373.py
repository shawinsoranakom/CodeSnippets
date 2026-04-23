async def list_agent_session(tenant_id, agent_id):
    if not UserCanvasService.query(user_id=tenant_id, id=agent_id):
        return get_error_data_result(message=f"You don't own the agent {agent_id}.")
    id = request.args.get("id")
    user_id = request.args.get("user_id")
    page_number = int(request.args.get("page", 1))
    items_per_page = int(request.args.get("page_size", 30))
    orderby = request.args.get("orderby", "update_time")
    if request.args.get("desc") == "False" or request.args.get("desc") == "false":
        desc = False
    else:
        desc = True
    # dsl defaults to True in all cases except for False and false
    include_dsl = request.args.get("dsl") != "False" and request.args.get("dsl") != "false"
    total, convs = API4ConversationService.get_list(agent_id, tenant_id, page_number, items_per_page, orderby, desc, id,
                                                    user_id, include_dsl)
    if not convs:
        return get_result(data=[])
    for conv in convs:
        conv["messages"] = conv.pop("message")
        infos = conv["messages"]
        for info in infos:
            if "prompt" in info:
                info.pop("prompt")
        conv["agent_id"] = conv.pop("dialog_id")
        # Fix for session listing endpoint
        if conv["reference"]:
            messages = conv["messages"]
            message_num = 0
            chunk_num = 0
            # Ensure reference is a list type to prevent KeyError
            if not isinstance(conv["reference"], list):
                conv["reference"] = []
            while message_num < len(messages):
                if message_num != 0 and messages[message_num]["role"] != "user":
                    chunk_list = []
                    # Add boundary and type checks to prevent KeyError
                    if chunk_num < len(conv["reference"]) and conv["reference"][chunk_num] is not None and isinstance(
                            conv["reference"][chunk_num], dict) and "chunks" in conv["reference"][chunk_num]:
                        chunks = conv["reference"][chunk_num]["chunks"]
                        for chunk in chunks:
                            # Ensure chunk is a dictionary before calling get method
                            if not isinstance(chunk, dict):
                                continue
                            new_chunk = {
                                "id": chunk.get("chunk_id", chunk.get("id")),
                                "content": chunk.get("content_with_weight", chunk.get("content")),
                                "document_id": chunk.get("doc_id", chunk.get("document_id")),
                                "document_name": chunk.get("docnm_kwd", chunk.get("document_name")),
                                "dataset_id": chunk.get("kb_id", chunk.get("dataset_id")),
                                "image_id": chunk.get("image_id", chunk.get("img_id")),
                                "positions": chunk.get("positions", chunk.get("position_int")),
                            }
                            chunk_list.append(new_chunk)
                    chunk_num += 1
                    messages[message_num]["reference"] = chunk_list
                message_num += 1
        del conv["reference"]
    return get_result(data=convs)