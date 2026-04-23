def predict(inputs:str, llm_kwargs:dict, plugin_kwargs:dict, chatbot:ChatBotWithCookies,
                history:list=[], system_prompt:str='', stream:bool=True, additional_fn:str=None):
        """
            refer to request_llms/bridge_all.py
        """
        chatbot.append((inputs, ""))

        _llm_handle = GetSingletonHandle().get_llm_model_instance(LLMSingletonClass)
        chatbot[-1] = (inputs, load_message + "\n\n" + _llm_handle.get_state())
        yield from update_ui(chatbot=chatbot, history=[])
        if not _llm_handle.running:
            raise RuntimeError(_llm_handle.get_state())

        if additional_fn is not None:
            from core_functional import handle_core_functionality
            inputs, history = handle_core_functionality(
                additional_fn, inputs, history, chatbot)

        # 处理历史信息
        if history_format == 'classic':
            # 没有 sys_prompt 接口，因此把prompt加入 history
            history_feedin = []
            history_feedin.append([system_prompt, "Certainly!"])
            for i in range(len(history)//2):
                history_feedin.append([history[2*i], history[2*i+1]])
        elif history_format == 'chatglm3':
            # 有 sys_prompt 接口
            conversation_cnt = len(history) // 2
            history_feedin = [{"role": "system", "content": system_prompt}]
            if conversation_cnt:
                for index in range(0, 2*conversation_cnt, 2):
                    what_i_have_asked = {}
                    what_i_have_asked["role"] = "user"
                    what_i_have_asked["content"] = history[index]
                    what_gpt_answer = {}
                    what_gpt_answer["role"] = "assistant"
                    what_gpt_answer["content"] = history[index+1]
                    if what_i_have_asked["content"] != "":
                        if what_gpt_answer["content"] == "":
                            continue
                        history_feedin.append(what_i_have_asked)
                        history_feedin.append(what_gpt_answer)
                    else:
                        history_feedin[-1]['content'] = what_gpt_answer['content']

        # 开始接收回复
        response = f"[Local Message] 等待{model_name}响应中 ..."
        for response in _llm_handle.stream_chat(query=inputs, history=history_feedin, max_length=llm_kwargs['max_length'], top_p=llm_kwargs['top_p'], temperature=llm_kwargs['temperature']):
            chatbot[-1] = (inputs, response)
            yield from update_ui(chatbot=chatbot, history=history)

        # 总结输出
        if response == f"[Local Message] 等待{model_name}响应中 ...":
            response = f"[Local Message] {model_name}响应异常 ..."
        history.extend([inputs, response])
        yield from update_ui(chatbot=chatbot, history=history)