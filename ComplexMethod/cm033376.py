async def related_questions_embedded():
    token = request.headers.get("Authorization").split()
    if len(token) != 2:
        return get_error_data_result(message='Authorization is not valid!')
    token = token[1]
    objs = APIToken.query(beta=token)
    if not objs:
        return get_error_data_result(message='Authentication error: API key is invalid!"')

    req = await get_request_json()
    tenant_id = objs[0].tenant_id
    if not tenant_id:
        return get_error_data_result(message="permission denined.")

    search_id = req.get("search_id", "")
    search_config = {}
    if search_id:
        if search_app := SearchService.get_detail(search_id):
            search_config = search_app.get("search_config", {})

    question = req["question"]

    chat_id = search_config.get("chat_id", "")
    if chat_id:
        chat_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.CHAT, chat_id)
    else:
        chat_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.CHAT)
    chat_mdl = LLMBundle(tenant_id, chat_model_config)

    gen_conf = search_config.get("llm_setting", {"temperature": 0.9})
    prompt = load_prompt("related_question")
    ans = await chat_mdl.async_chat(
        prompt,
        [
            {
                "role": "user",
                "content": f"""
Keywords: {question}
Related search terms:
    """,
            }
        ],
        gen_conf,
    )
    return get_json_result(data=[re.sub(r"^[0-9]\. ", "", a) for a in ans.split("\n") if re.match(r"^[0-9]\. ", a)])