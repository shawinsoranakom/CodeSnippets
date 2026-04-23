def predict(inputs:str, llm_kwargs:dict, plugin_kwargs:dict, chatbot:ChatBotWithCookies,
            history:list=[], system_prompt:str='', stream:bool=True, additional_fn:str=None):

    from .bridge_all import model_info

    # 检查API_KEY
    if get_conf("GEMINI_API_KEY") == "":
        yield from update_ui_latest_msg(f"请配置 GEMINI_API_KEY。", chatbot=chatbot, history=history, delay=0)
        return

    # 适配润色区域
    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    # multimodal capacity
    # inspired by codes in bridge_chatgpt
    has_multimodal_capacity = model_info[llm_kwargs['llm_model']].get('has_multimodal_capacity', False)
    if has_multimodal_capacity:
        has_recent_image_upload, image_paths = have_any_recent_upload_image_files(chatbot, pop=True)
    else:
        has_recent_image_upload, image_paths = False, []
    if has_recent_image_upload:
        inputs, image_base64_array = make_media_input(inputs, image_paths)
    else:
        inputs, image_base64_array = inputs, []

    chatbot.append((inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history)
    genai = GoogleChatInit(llm_kwargs)
    retry = 0
    while True:
        try:
            stream_response = genai.generate_chat(inputs, llm_kwargs, history, system_prompt, image_base64_array, has_multimodal_capacity)
            break
        except Exception as e:
            retry += 1
            chatbot[-1] = ((chatbot[-1][0], trimmed_format_exc()))
            yield from update_ui(chatbot=chatbot, history=history, msg="请求失败")  # 刷新界面
            return
    gpt_replying_buffer = ""
    gpt_security_policy = ""
    history.extend([inputs, ''])
    for response in stream_response:
        results = response.decode("utf-8")    # 被这个解码给耍了。。
        gpt_security_policy += results
        match = re.search(r'"text":\s*"((?:[^"\\]|\\.)*)"', results, flags=re.DOTALL)
        error_match = re.search(r'\"message\":\s*\"(.*)\"', results, flags=re.DOTALL)
        if match:
            try:
                paraphrase = json.loads('{"text": "%s"}' % match.group(1))
            except:
                raise ValueError(f"解析GEMINI消息出错。")
            gpt_replying_buffer += paraphrase['text']    # 使用 json 解析库进行处理
            chatbot[-1] = (inputs, gpt_replying_buffer)
            history[-1] = gpt_replying_buffer
            log_chat(llm_model=llm_kwargs["llm_model"], input_str=inputs, output_str=gpt_replying_buffer)
            yield from update_ui(chatbot=chatbot, history=history)
        if error_match:
            history = history[-2]  # 错误的不纳入对话
            chatbot[-1] = (inputs, gpt_replying_buffer + f"对话错误，请查看message\n\n```\n{error_match.group(1)}\n```")
            yield from update_ui(chatbot=chatbot, history=history)
            raise RuntimeError('对话错误')
    if not gpt_replying_buffer:
        history = history[-2]  # 错误的不纳入对话
        chatbot[-1] = (inputs, gpt_replying_buffer + f"触发了Google的安全访问策略，没有回答\n\n```\n{gpt_security_policy}\n```")
        yield from update_ui(chatbot=chatbot, history=history)