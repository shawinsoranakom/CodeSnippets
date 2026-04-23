def generate_payload(inputs:str, llm_kwargs:dict, history:list, system_prompt:str, image_base64_array:list=[], has_multimodal_capacity:bool=False, stream:bool=True):
    """
    整合所有信息，选择LLM模型，生成http请求，为发送请求做准备
    """
    from request_llms.bridge_all import model_info

    if not is_any_api_key(llm_kwargs['api_key']):
        raise AssertionError("你提供了错误的API_KEY。\n\n1. 临时解决方案：直接在输入区键入api_key，然后回车提交。\n\n2. 长效解决方案：在config.py中配置。")

    if llm_kwargs['llm_model'].startswith('vllm-'):
        api_key = 'no-api-key'
    else:
        api_key = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    if API_ORG.startswith('org-'): headers.update({"OpenAI-Organization": API_ORG})
    if llm_kwargs['llm_model'].startswith('azure-'):
        headers.update({"api-key": api_key})
        if llm_kwargs['llm_model'] in AZURE_CFG_ARRAY.keys():
            azure_api_key_unshared = AZURE_CFG_ARRAY[llm_kwargs['llm_model']]["AZURE_API_KEY"]
            headers.update({"api-key": azure_api_key_unshared})

    if has_multimodal_capacity:
        # 当以下条件满足时，启用多模态能力：
        # 1. 模型本身是多模态模型（has_multimodal_capacity）
        # 2. 输入包含图像（len(image_base64_array) > 0）
        # 3. 历史输入包含图像（ any([contain_base64(h) for h in history]) ）
        enable_multimodal_capacity = (len(image_base64_array) > 0) or any([contain_base64(h) for h in history])
    else:
        enable_multimodal_capacity = False

    conversation_cnt = len(history) // 2
    openai_disable_system_prompt = model_info[llm_kwargs['llm_model']].get('openai_disable_system_prompt', False)

    if openai_disable_system_prompt:
        messages = [{"role": "user", "content": system_prompt}]
    else:
        messages = [{"role": "system", "content": system_prompt}]

    if not enable_multimodal_capacity:
        # 不使用多模态能力
        if conversation_cnt:
            for index in range(0, 2*conversation_cnt, 2):
                what_i_have_asked = {}
                what_i_have_asked["role"] = "user"
                what_i_have_asked["content"] = remove_image_if_contain_base64(history[index])
                what_gpt_answer = {}
                what_gpt_answer["role"] = "assistant"
                what_gpt_answer["content"] = remove_image_if_contain_base64(history[index+1])
                if what_i_have_asked["content"] != "":
                    if what_gpt_answer["content"] == "": continue
                    if what_gpt_answer["content"] == timeout_bot_msg: continue
                    messages.append(what_i_have_asked)
                    messages.append(what_gpt_answer)
                else:
                    messages[-1]['content'] = what_gpt_answer['content']
        what_i_ask_now = {}
        what_i_ask_now["role"] = "user"
        what_i_ask_now["content"] = inputs
        messages.append(what_i_ask_now)
    else:
        # 多模态能力
        if conversation_cnt:
            for index in range(0, 2*conversation_cnt, 2):
                what_i_have_asked = {}
                what_i_have_asked["role"] = "user"
                what_i_have_asked["content"] = append_image_if_contain_base64(history[index])
                what_gpt_answer = {}
                what_gpt_answer["role"] = "assistant"
                what_gpt_answer["content"] = append_image_if_contain_base64(history[index+1])
                if what_i_have_asked["content"] != "":
                    if what_gpt_answer["content"] == "": continue
                    if what_gpt_answer["content"] == timeout_bot_msg: continue
                    messages.append(what_i_have_asked)
                    messages.append(what_gpt_answer)
                else:
                    messages[-1]['content'] = what_gpt_answer['content']
        what_i_ask_now = {}
        what_i_ask_now["role"] = "user"
        what_i_ask_now["content"] = []
        what_i_ask_now["content"].append({
            "type": "text",
            "text": inputs
        })
        for image_base64 in image_base64_array:
            what_i_ask_now["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            })
        messages.append(what_i_ask_now)


    model = llm_kwargs['llm_model']
    if llm_kwargs['llm_model'].startswith('api2d-'):
        model = llm_kwargs['llm_model'][len('api2d-'):]
    if llm_kwargs['llm_model'].startswith('one-api-'):
        model = llm_kwargs['llm_model'][len('one-api-'):]
        model, _ = read_one_api_model_name(model)
    if llm_kwargs['llm_model'].startswith('vllm-'):
        model = llm_kwargs['llm_model'][len('vllm-'):]
        model, _ = read_one_api_model_name(model)
    if model == "gpt-3.5-random": # 随机选择, 绕过openai访问频率限制
        model = random.choice([
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-3.5-turbo-0301",
        ])

    payload = {
        "model": model,
        "messages": messages,
        "temperature": llm_kwargs['temperature'],  # 1.0,
        "top_p": llm_kwargs['top_p'],  # 1.0,
        "n": 1,
        "stream": stream,
    }
    openai_force_temperature_one = model_info[llm_kwargs['llm_model']].get('openai_force_temperature_one', False)
    if openai_force_temperature_one:
        payload.pop('temperature')
    return headers,payload