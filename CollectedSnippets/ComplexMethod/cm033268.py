async def completion(tenant_id, agent_id, session_id=None, **kwargs):
    query = kwargs.get("query", "") or kwargs.get("question", "")
    files = kwargs.get("files", [])
    inputs = kwargs.get("inputs", {})
    user_id = kwargs.get("user_id", "")
    custom_header = kwargs.get("custom_header", "")
    release_mode = str(kwargs.get("release", "")).strip().lower()

    if session_id:
        e, conv = API4ConversationService.get_by_id(session_id)
        if not e:
            raise LookupError("Session not found!")
        if not conv.message:
            conv.message = []
        if not isinstance(conv.dsl, str):
            conv.dsl = json.dumps(conv.dsl, ensure_ascii=False)
        canvas = Canvas(conv.dsl, tenant_id, agent_id, canvas_id=agent_id, custom_header=custom_header)
    else:
        cvs, dsl = UserCanvasService.get_agent_dsl_with_release(agent_id, release_mode=release_mode == "true", tenant_id=tenant_id)

        session_id = get_uuid()
        canvas = Canvas(dsl, tenant_id, agent_id, canvas_id=cvs.id, custom_header=custom_header)
        canvas.reset()
        # Get the version title based on release_mode
        version_title = UserCanvasVersionService.get_latest_version_title(cvs.id, release_mode=release_mode == "true")
        conv = {"id": session_id, "dialog_id": cvs.id, "user_id": user_id, "message": [], "source": "agent", "dsl": dsl, "reference": [], "version_title": version_title}
        API4ConversationService.save(**conv)
        conv = API4Conversation(**conv)

    message_id = str(uuid4())
    conv.message.append({
        "role": "user",
        "content": query,
        "id": message_id,
        "files": files
    })
    txt = ""
    async for ans in canvas.run(query=query, files=files, user_id=user_id, inputs=inputs):
        ans["session_id"] = session_id
        if ans["event"] == "message":
            txt += ans["data"]["content"]
            if ans["data"].get("start_to_think", False):
                txt += "<think>"
            elif ans["data"].get("end_to_think", False):
                txt += "</think>"
        yield "data:" + json.dumps(ans, ensure_ascii=False) + "\n\n"

    conv.message.append({"role": "assistant", "content": txt, "created_at": time.time(), "id": message_id})
    conv.reference = canvas.get_reference()
    conv.errors = canvas.error
    conv.dsl = str(canvas)
    conv = conv.to_dict()
    API4ConversationService.append_message(conv["id"], conv)