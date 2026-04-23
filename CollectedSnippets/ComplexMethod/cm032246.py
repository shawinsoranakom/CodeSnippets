def predict_no_ui_long_connection(inputs:str, llm_kwargs:dict, history:list, sys_prompt:str, observe_window:list=[], console_silence:bool=False):
    """
    发送至LLM，等待回复，一次性完成，不显示中间过程。但内部（尽可能地）用stream的方法避免中途网线被掐。
    inputs：
        是本次问询的输入
    sys_prompt:
        系统静默prompt
    llm_kwargs：
        LLM的内部调优参数
    history：
        是之前的对话列表
    observe_window = None：
        用于负责跨越线程传递已经输出的部分，大部分时候仅仅为了fancy的视觉效果，留空即可。observe_window[0]：观测窗。observe_window[1]：看门狗
    """
    import threading, time, copy

    inputs = apply_gpt_academic_string_mask(inputs, mode="show_llm")
    model = llm_kwargs['llm_model']
    n_model = 1
    if '&' not in model:
        # 如果只询问“一个”大语言模型（多数情况）：
        method = model_info[model]["fn_without_ui"]
        return method(inputs, llm_kwargs, history, sys_prompt, observe_window, console_silence)
    else:
        # 如果同时询问“多个”大语言模型，这个稍微啰嗦一点，但思路相同，您不必读这个else分支
        executor = ThreadPoolExecutor(max_workers=4)
        models = model.split('&')
        n_model = len(models)

        window_len = len(observe_window)
        assert window_len==3
        window_mutex = [["", time.time(), ""] for _ in range(n_model)] + [True]

        futures = []
        for i in range(n_model):
            model = models[i]
            method = model_info[model]["fn_without_ui"]
            llm_kwargs_feedin = copy.deepcopy(llm_kwargs)
            llm_kwargs_feedin['llm_model'] = model
            future = executor.submit(LLM_CATCH_EXCEPTION(method), inputs, llm_kwargs_feedin, history, sys_prompt, window_mutex[i], console_silence)
            futures.append(future)

        def mutex_manager(window_mutex, observe_window):
            while True:
                time.sleep(0.25)
                if not window_mutex[-1]: break
                # 看门狗（watchdog）
                for i in range(n_model):
                    window_mutex[i][1] = observe_window[1]
                # 观察窗（window）
                chat_string = []
                for i in range(n_model):
                    color = colors[i%len(colors)]
                    chat_string.append( f"【{str(models[i])} 说】: <font color=\"{color}\"> {window_mutex[i][0]} </font>" )
                res = '<br/><br/>\n\n---\n\n'.join(chat_string)
                # # # # # # # # # # #
                observe_window[0] = res

        t_model = threading.Thread(target=mutex_manager, args=(window_mutex, observe_window), daemon=True)
        t_model.start()

        return_string_collect = []
        while True:
            worker_done = [h.done() for h in futures]
            if all(worker_done):
                executor.shutdown()
                break
            time.sleep(1)

        for i, future in enumerate(futures):  # wait and get
            color = colors[i%len(colors)]
            return_string_collect.append( f"【{str(models[i])} 说】: <font color=\"{color}\"> {future.result()} </font>" )

        window_mutex[-1] = False # stop mutex thread
        res = '<br/><br/>\n\n---\n\n'.join(return_string_collect)
        return res