def setup_initial_com(initial_msg: UserInterfaceMsg):
    """
    设置插件参数

    从初始消息中提取各种参数并构建插件执行所需的参数字典。

    参数:
        initial_msg: 初始的用户消息
        chatbot_with_cookies: 带有cookie的聊天机器人实例

    返回:
        dict: 包含插件执行所需所有参数的字典
    """
    from toolbox import get_plugin_default_kwargs


    com = get_plugin_default_kwargs()
    com["main_input"] = initial_msg.main_input
    # 设置LLM相关参数
    if initial_msg.llm_kwargs.get('api_key', None):     com["llm_kwargs"]['api_key'] = initial_msg.llm_kwargs.get('api_key')
    if initial_msg.llm_kwargs.get('llm_model', None):   com["llm_kwargs"]['llm_model'] = initial_msg.llm_kwargs.get('llm_model')
    if initial_msg.llm_kwargs.get('top_p', None):       com["llm_kwargs"]['top_p'] = initial_msg.llm_kwargs.get('top_p')
    if initial_msg.llm_kwargs.get('max_length', None):  com["llm_kwargs"]['max_length'] = initial_msg.llm_kwargs.get('max_length')
    if initial_msg.llm_kwargs.get('temperature', None): com["llm_kwargs"]['temperature'] = initial_msg.llm_kwargs.get('temperature')
    if initial_msg.llm_kwargs.get('user_name', None):   com["llm_kwargs"]['user_name'] = initial_msg.llm_kwargs.get('user_name')
    if initial_msg.llm_kwargs.get('embed_model', None): com["llm_kwargs"]['embed_model'] = initial_msg.llm_kwargs.get('embed_model')

    initial_msg.chatbot_cookies.update({
        'api_key':      com["llm_kwargs"]['api_key'],
        'top_p':        com["llm_kwargs"]['top_p'],
        'llm_model':    com["llm_kwargs"]['llm_model'],
        'embed_model':  com["llm_kwargs"]['embed_model'],
        'temperature':  com["llm_kwargs"]['temperature'],
        'user_name':    com["llm_kwargs"]['user_name'],
        'customize_fn_overwrite': {},
    })
    chatbot_with_cookies = ChatBotWithCookies(initial_msg.chatbot_cookies)
    chatbot_with_cookies.write_list(initial_msg.chatbot)
    # 设置其他参数
    com["plugin_kwargs"] = initial_msg.plugin_kwargs
    com["chatbot_with_cookie"] = chatbot_with_cookies
    com["history"] = initial_msg.history
    com["system_prompt"] = initial_msg.system_prompt
    com["user_request"] = initial_msg.user_request

    return com