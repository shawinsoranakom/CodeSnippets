def generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths):
    """
    整合所有信息，选择LLM模型，生成http请求，为发送请求做准备
    """

    conversation_cnt = len(history) // 2

    messages = []

    if conversation_cnt:
        for index in range(0, 2*conversation_cnt, 2):
            what_i_have_asked = {}
            what_i_have_asked["role"] = "user"
            what_i_have_asked["content"] = [{"type": "text", "text": history[index]}]
            what_gpt_answer = {}
            what_gpt_answer["role"] = "assistant"
            what_gpt_answer["content"] = [{"type": "text", "text": history[index+1]}]
            if what_i_have_asked["content"][0]["text"] != "":
                if what_i_have_asked["content"][0]["text"] == "": continue
                if what_i_have_asked["content"][0]["text"] == timeout_bot_msg: continue
                messages.append(what_i_have_asked)
                messages.append(what_gpt_answer)
            else:
                messages[-1]['content'][0]['text'] = what_gpt_answer['content'][0]['text']

    if any([llm_kwargs['llm_model'] == model for model in Claude_3_Models]) and image_paths:
        what_i_ask_now = {}
        what_i_ask_now["role"] = "user"
        what_i_ask_now["content"] = []
        for image_path in image_paths:
            what_i_ask_now["content"].append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": multiple_picture_types(image_paths),
                    "data": encode_image(image_path),
                }
            })
        what_i_ask_now["content"].append({"type": "text", "text": inputs})
    else:
        what_i_ask_now = {}
        what_i_ask_now["role"] = "user"
        what_i_ask_now["content"] = [{"type": "text", "text": inputs}]
    messages.append(what_i_ask_now)
    # 开始整理headers与message
    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    payload = {
        'model': llm_kwargs['llm_model'],
        'max_tokens': 4096,
        'messages': messages,
        'temperature': llm_kwargs['temperature'],
        'stream': True,
        'system': system_prompt
    }
    return headers, payload