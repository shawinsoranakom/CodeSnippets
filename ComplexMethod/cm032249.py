def predict(
    inputs,
    llm_kwargs,
    plugin_kwargs,
    chatbot,
    history=[],
    system_prompt="",
    stream=True,
    additional_fn=None,
):
    """
    单线程方法
    函数的说明请见 request_llms/bridge_all.py
    """
    chatbot.append((inputs, "[Local Message] 等待Claude响应中 ..."))

    global claude_handle
    if (claude_handle is None) or (not claude_handle.success):
        claude_handle = ClaudeHandle()
        chatbot[-1] = (inputs, load_message + "\n\n" + claude_handle.info)
        yield from update_ui(chatbot=chatbot, history=[])
        if not claude_handle.success:
            claude_handle = None
            return

    if additional_fn is not None:
        from core_functional import handle_core_functionality

        inputs, history = handle_core_functionality(
            additional_fn, inputs, history, chatbot
        )

    history_feedin = []
    for i in range(len(history) // 2):
        history_feedin.append([history[2 * i], history[2 * i + 1]])

    chatbot[-1] = (inputs, "[Local Message] 等待Claude响应中 ...")
    response = "[Local Message] 等待Claude响应中 ..."
    yield from update_ui(
        chatbot=chatbot, history=history, msg="Claude响应缓慢，尚未完成全部响应，请耐心完成后再提交新问题。"
    )
    for response in claude_handle.stream_chat(
        query=inputs, history=history_feedin, system_prompt=system_prompt
    ):
        chatbot[-1] = (inputs, preprocess_newbing_out(response))
        yield from update_ui(
            chatbot=chatbot, history=history, msg="Claude响应缓慢，尚未完成全部响应，请耐心完成后再提交新问题。"
        )
    if response == "[Local Message] 等待Claude响应中 ...":
        response = "[Local Message] Claude响应异常，请刷新界面重试 ..."
    history.extend([inputs, response])
    logging.info(f"[raw_input] {inputs}")
    logging.info(f"[response] {response}")
    yield from update_ui(chatbot=chatbot, history=history, msg="完成全部响应，请提交新问题。")