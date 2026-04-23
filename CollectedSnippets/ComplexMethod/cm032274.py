def generate_payload(inputs, llm_kwargs, history, system_prompt, stream):
    """
    整合所有信息，选择LLM模型，生成http请求，为发送请求做准备
    """
    # if not is_any_api_key(llm_kwargs['api_key']):
    #     raise AssertionError("你提供了错误的API_KEY。\n\n1. 临时解决方案：直接在输入区键入api_key，然后回车提交。\n\n2. 长效解决方案：在config.py中配置。")

    api_key = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    if API_ORG.startswith('org-'): headers.update({"Cohere-Organization": API_ORG})
    if llm_kwargs['llm_model'].startswith('azure-'):
        headers.update({"api-key": api_key})
        if llm_kwargs['llm_model'] in AZURE_CFG_ARRAY.keys():
            azure_api_key_unshared = AZURE_CFG_ARRAY[llm_kwargs['llm_model']]["AZURE_API_KEY"]
            headers.update({"api-key": azure_api_key_unshared})

    conversation_cnt = len(history) // 2

    messages = [{"role": "SYSTEM", "message": system_prompt}]
    if conversation_cnt:
        for index in range(0, 2*conversation_cnt, 2):
            what_i_have_asked = {}
            what_i_have_asked["role"] = "USER"
            what_i_have_asked["message"] = history[index]
            what_gpt_answer = {}
            what_gpt_answer["role"] = "CHATBOT"
            what_gpt_answer["message"] = history[index+1]
            if what_i_have_asked["message"] != "":
                if what_gpt_answer["message"] == "": continue
                if what_gpt_answer["message"] == timeout_bot_msg: continue
                messages.append(what_i_have_asked)
                messages.append(what_gpt_answer)
            else:
                messages[-1]['message'] = what_gpt_answer['message']

    model = llm_kwargs['llm_model']
    if model.startswith('cohere-'): model = model[len('cohere-'):]
    payload = {
        "model": model,
        "message": inputs,
        "chat_history": messages,
        "temperature": llm_kwargs['temperature'],  # 1.0,
        "top_p": llm_kwargs['top_p'],  # 1.0,
        "n": 1,
        "stream": stream,
        "presence_penalty": 0,
        "frequency_penalty": 0,
    }

    return headers,payload