def predict_no_ui_long_connection(inputs:str, llm_kwargs:dict, history:list=[], sys_prompt:str="", observe_window:list=[],
                                  console_silence:bool=False):
    # 检查API_KEY
    if get_conf("GEMINI_API_KEY") == "":
        raise ValueError(f"请配置 GEMINI_API_KEY。")

    genai = GoogleChatInit(llm_kwargs)
    watch_dog_patience = 5  # 看门狗的耐心, 设置5秒即可
    gpt_replying_buffer = ''
    stream_response = genai.generate_chat(inputs, llm_kwargs, history, sys_prompt)
    for response in stream_response:
        results = response.decode()
        match = re.search(r'"text":\s*"((?:[^"\\]|\\.)*)"', results, flags=re.DOTALL)
        error_match = re.search(r'\"message\":\s*\"(.*?)\"', results, flags=re.DOTALL)
        if match:
            try:
                paraphrase = json.loads('{"text": "%s"}' % match.group(1))
            except:
                raise ValueError(f"解析GEMINI消息出错。")
            buffer = paraphrase['text']
            gpt_replying_buffer += buffer
            if len(observe_window) >= 1:
                observe_window[0] = gpt_replying_buffer
            if len(observe_window) >= 2:
                if (time.time() - observe_window[1]) > watch_dog_patience: raise RuntimeError("程序终止。")
        if error_match:
            raise RuntimeError(f'{gpt_replying_buffer} 对话错误')
    return gpt_replying_buffer