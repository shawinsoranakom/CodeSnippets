def predict_no_ui_long_connection(inputs:str, llm_kwargs:dict, history:list=[], sys_prompt:str="",
                                  observe_window:list=[], console_silence:bool=False):
    """
        多线程方法
        函数的说明请见 request_llms/bridge_all.py
    """
    global llama_glm_handle
    if llama_glm_handle is None:
        llama_glm_handle = GetGLMHandle()
        if len(observe_window) >= 1: observe_window[0] = load_message + "\n\n" + llama_glm_handle.info
        if not llama_glm_handle.success:
            error = llama_glm_handle.info
            llama_glm_handle = None
            raise RuntimeError(error)

    # jittorllms 没有 sys_prompt 接口，因此把prompt加入 history
    history_feedin = []
    for i in range(len(history)//2):
        history_feedin.append([history[2*i], history[2*i+1]] )

    watch_dog_patience = 5 # 看门狗 (watchdog) 的耐心, 设置5秒即可
    response = ""
    for response in llama_glm_handle.stream_chat(query=inputs, history=history_feedin, system_prompt=sys_prompt, max_length=llm_kwargs['max_length'], top_p=llm_kwargs['top_p'], temperature=llm_kwargs['temperature']):
        print(response)
        if len(observe_window) >= 1:  observe_window[0] = response
        if len(observe_window) >= 2:
            if (time.time()-observe_window[1]) > watch_dog_patience:
                raise RuntimeError("程序终止。")
    return response