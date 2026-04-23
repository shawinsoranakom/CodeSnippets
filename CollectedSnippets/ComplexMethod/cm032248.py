def predict_no_ui_long_connection(
    inputs,
    llm_kwargs,
    history=[],
    sys_prompt="",
    observe_window=None,
    console_silence=False,
):
    """
    多线程方法
    函数的说明请见 request_llms/bridge_all.py
    """
    global claude_handle
    if (claude_handle is None) or (not claude_handle.success):
        claude_handle = ClaudeHandle()
        observe_window[0] = load_message + "\n\n" + claude_handle.info
        if not claude_handle.success:
            error = claude_handle.info
            claude_handle = None
            raise RuntimeError(error)

    # 没有 sys_prompt 接口，因此把prompt加入 history
    history_feedin = []
    for i in range(len(history) // 2):
        history_feedin.append([history[2 * i], history[2 * i + 1]])

    watch_dog_patience = 5  # 看门狗 (watchdog) 的耐心, 设置5秒即可
    response = ""
    observe_window[0] = "[Local Message] 等待Claude响应中 ..."
    for response in claude_handle.stream_chat(
        query=inputs,
        history=history_feedin,
        system_prompt=sys_prompt,
        max_length=llm_kwargs["max_length"],
        top_p=llm_kwargs["top_p"],
        temperature=llm_kwargs["temperature"],
    ):
        observe_window[0] = preprocess_newbing_out_simple(response)
        if len(observe_window) >= 2:
            if (time.time() - observe_window[1]) > watch_dog_patience:
                raise RuntimeError("程序终止。")
    return preprocess_newbing_out_simple(response)