def predict_no_ui_long_connection(inputs:str, llm_kwargs:dict, history:list=[], sys_prompt:str="", observe_window:list=[], console_silence:bool=False):
        """
            refer to request_llms/bridge_all.py
        """
        _llm_handle = GetSingletonHandle().get_llm_model_instance(LLMSingletonClass)
        if len(observe_window) >= 1:
            observe_window[0] = load_message + "\n\n" + _llm_handle.get_state()
        if not _llm_handle.running:
            raise RuntimeError(_llm_handle.get_state())

        if history_format == 'classic':
            # 没有 sys_prompt 接口，因此把prompt加入 history
            history_feedin = []
            history_feedin.append([sys_prompt, "Certainly!"])
            for i in range(len(history)//2):
                history_feedin.append([history[2*i], history[2*i+1]])
        elif history_format == 'chatglm3':
            # 有 sys_prompt 接口
            conversation_cnt = len(history) // 2
            history_feedin = [{"role": "system", "content": sys_prompt}]
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

        watch_dog_patience = 5  # 看门狗 (watchdog) 的耐心, 设置5秒即可
        response = ""
        for response in _llm_handle.stream_chat(query=inputs, history=history_feedin, max_length=llm_kwargs['max_length'], top_p=llm_kwargs['top_p'], temperature=llm_kwargs['temperature']):
            if len(observe_window) >= 1:
                observe_window[0] = response
            if len(observe_window) >= 2:
                if (time.time()-observe_window[1]) > watch_dog_patience:
                    raise RuntimeError("程序终止。")
        return response