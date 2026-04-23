def predict_no_ui_long_connection(inputs:str, llm_kwargs:dict, history:list=[], sys_prompt:str="",
                                  observe_window:list=[], console_silence:bool=False):
    """
        多线程方法
        函数的说明请见 request_llms/bridge_all.py
    """
    global moss_handle
    if moss_handle is None:
        moss_handle = GetGLMHandle()
        if len(observe_window) >= 1: observe_window[0] = load_message + "\n\n" + moss_handle.info
        if not moss_handle.success:
            error = moss_handle.info
            moss_handle = None
            raise RuntimeError(error)

    # chatglm 没有 sys_prompt 接口，因此把prompt加入 history
    history_feedin = []
    for i in range(len(history)//2):
        history_feedin.append([history[2*i], history[2*i+1]] )

    watch_dog_patience = 5 # 看门狗 (watchdog) 的耐心, 设置5秒即可
    response = ""
    for response in moss_handle.stream_chat(query=inputs, history=history_feedin, sys_prompt=sys_prompt, max_length=llm_kwargs['max_length'], top_p=llm_kwargs['top_p'], temperature=llm_kwargs['temperature']):
        if len(observe_window) >= 1:  observe_window[0] = response
        if len(observe_window) >= 2:
            if (time.time()-observe_window[1]) > watch_dog_patience:
                raise RuntimeError("程序终止。")
    return response