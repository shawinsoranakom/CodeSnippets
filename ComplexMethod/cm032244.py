def generate_message_payload(inputs, llm_kwargs, history, system_prompt, file_manifest):
    conversation_cnt = len(history) // 2
    messages = []
    if file_manifest:
        base64_images = []
        for image_path in file_manifest:
            base64_images.append(encode_image(image_path))
        for img_s in base64_images:
            if img_s not in str(messages):
                messages.append({"role": "user", "content": img_s, "content_type": "image"})
    else:
        messages = [{"role": "system", "content": system_prompt}]
    if conversation_cnt:
        for index in range(0, 2*conversation_cnt, 2):
            what_i_have_asked = {}
            what_i_have_asked["role"] = "user"
            what_i_have_asked["content"] = history[index]
            what_gpt_answer = {}
            what_gpt_answer["role"] = "assistant"
            what_gpt_answer["content"] = history[index+1]
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
    return messages