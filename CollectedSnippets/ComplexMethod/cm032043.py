def Multi_Agent_Legacy终端(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             输入栏用户输入的文本，例如需要翻译的一段话，再例如一个包含了待处理文件的路径
    llm_kwargs      gpt模型参数，如温度和top_p等，一般原样传递下去就行
    plugin_kwargs   插件模型的参数
    chatbot         聊天显示框的句柄，用于显示给用户
    history         聊天历史，前情提要
    system_prompt   给gpt的静默提醒
    user_request    当前用户的请求信息（IP地址等）
    """
    # 检查当前的模型是否符合要求
    supported_llms = [
        "gpt-3.5-turbo-16k",
        'gpt-3.5-turbo-1106',
        "gpt-4",
        "gpt-4-32k",
        'gpt-4-1106-preview',
        "azure-gpt-3.5-turbo-16k",
        "azure-gpt-3.5-16k",
        "azure-gpt-4",
        "azure-gpt-4-32k",
    ]
    from request_llms.bridge_all import model_info
    if model_info[llm_kwargs['llm_model']]["max_token"] < 8000: # 至少是8k上下文的模型
        chatbot.append([f"处理任务: {txt}", f"当前插件只支持{str(supported_llms)}, 当前模型{llm_kwargs['llm_model']}的最大上下文长度太短, 不能支撑AutoGen运行。"])
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return
    if model_info[llm_kwargs['llm_model']]["endpoint"] is not None: # 如果不是本地模型，加载API_KEY
        llm_kwargs['api_key'] = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])

    # 尝试导入依赖，如果缺少依赖，则给出安装建议
    try:
        import autogen
        if get_conf("AUTOGEN_USE_DOCKER"):
            import docker
    except:
        chatbot.append([ f"处理任务: {txt}",
            f"导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade pyautogen docker```。"])
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return

    # 尝试导入依赖，如果缺少依赖，则给出安装建议
    try:
        import autogen
        import glob, os, time, subprocess
        if get_conf("AUTOGEN_USE_DOCKER"):
            subprocess.Popen(["docker", "--version"])
    except:
        chatbot.append([f"处理任务: {txt}", f"缺少docker运行环境！"])
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return

    # 解锁插件
    chatbot.get_cookies()['lock_plugin'] = None
    persistent_class_multi_user_manager = GradioMultiuserManagerForPersistentClasses()
    user_uuid = chatbot.get_cookies().get('uuid')
    persistent_key = f"{user_uuid}->Multi_Agent_Legacy终端"
    if persistent_class_multi_user_manager.already_alive(persistent_key):
        # 当已经存在一个正在运行的Multi_Agent_Legacy终端时，直接将用户输入传递给它，而不是再次启动一个新的Multi_Agent_Legacy终端
        logger.info('[debug] feed new user input')
        executor = persistent_class_multi_user_manager.get(persistent_key)
        exit_reason = yield from executor.main_process_ui_control(txt, create_or_resume="resume")
    else:
        # 运行Multi_Agent_Legacy终端 (首次)
        logger.info('[debug] create new executor instance')
        history = []
        chatbot.append(["正在启动: Multi_Agent_Legacy终端", "插件动态生成, 执行开始, 作者 Microsoft & Binary-Husky."])
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        executor = AutoGenMath(llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request)
        persistent_class_multi_user_manager.set(persistent_key, executor)
        exit_reason = yield from executor.main_process_ui_control(txt, create_or_resume="create")

    if exit_reason == "wait_feedback":
        # 当用户点击了“等待反馈”按钮时，将executor存储到cookie中，等待用户的再次调用
        executor.chatbot.get_cookies()['lock_plugin'] = 'crazy_functions.Multi_Agent_Legacy->Multi_Agent_Legacy终端'
    else:
        executor.chatbot.get_cookies()['lock_plugin'] = None
    yield from update_ui(chatbot=executor.chatbot, history=executor.history)