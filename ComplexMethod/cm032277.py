def generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths):
    """
    整合所有信息，选择LLM模型，生成http请求，为发送请求做准备
    """
    if not is_any_api_key(llm_kwargs['api_key']):
        raise AssertionError("你提供了错误的API_KEY。\n\n1. 临时解决方案：直接在输入区键入api_key，然后回车提交。\n\n2. 长效解决方案：在config.py中配置。")

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

    base64_images = []
    for image_path in image_paths:
        base64_images.append(encode_image(image_path))

    messages = []
    what_i_ask_now = {}
    what_i_ask_now["role"] = "user"
    what_i_ask_now["content"] = []
    what_i_ask_now["content"].append({
        "type": "text",
        "text": inputs
    })

    for image_path, base64_image in zip(image_paths, base64_images):
        what_i_ask_now["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    messages.append(what_i_ask_now)
    model = llm_kwargs['llm_model']
    if llm_kwargs['llm_model'].startswith('api2d-'):
        model = llm_kwargs['llm_model'][len('api2d-'):]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": llm_kwargs['temperature'],   # 1.0,
        "top_p": llm_kwargs['top_p'],               # 1.0,
        "n": 1,
        "stream": True,
        "max_tokens": get_max_token(llm_kwargs),
        "presence_penalty": 0,
        "frequency_penalty": 0,
    }

    return headers, payload, api_key