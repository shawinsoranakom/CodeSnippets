def 解析历史输入(history, llm_kwargs, file_manifest, chatbot, plugin_kwargs):
    ############################## <第 0 步，切割输入> ##################################
    # 借用PDF切割中的函数对文本进行切割
    TOKEN_LIMIT_PER_FRAGMENT = 2500
    txt = (
        str(history).encode("utf-8", "ignore").decode()
    )  # avoid reading non-utf8 chars
    from crazy_functions.pdf_fns.breakdown_txt import (
        breakdown_text_to_satisfy_token_limit,
    )

    txt = breakdown_text_to_satisfy_token_limit(
        txt=txt, limit=TOKEN_LIMIT_PER_FRAGMENT, llm_model=llm_kwargs["llm_model"]
    )
    ############################## <第 1 步，迭代地历遍整个文章，提取精炼信息> ##################################
    results = []
    MAX_WORD_TOTAL = 4096
    n_txt = len(txt)
    last_iteration_result = "从以下文本中提取摘要。"

    for i in range(n_txt):
        NUM_OF_WORD = MAX_WORD_TOTAL // n_txt
        i_say = f"Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words in Chinese: {txt[i]}"
        i_say_show_user = f"[{i+1}/{n_txt}] Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {txt[i][:200]} ...."
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
            i_say,
            i_say_show_user,  # i_say=真正给chatgpt的提问， i_say_show_user=给用户看的提问
            llm_kwargs,
            chatbot,
            history=[
                "The main content of the previous section is?",
                last_iteration_result,
            ],  # 迭代上一次的结果
            sys_prompt="Extracts the main content from the text section where it is located for graphing purposes, answer me with Chinese.",  # 提示
        )
        results.append(gpt_say)
        last_iteration_result = gpt_say
    ############################## <第 2 步，根据整理的摘要选择图表类型> ##################################
    gpt_say = str(plugin_kwargs)  # 将图表类型参数赋值为插件参数
    results_txt = "\n".join(results)  # 合并摘要
    if gpt_say not in [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    ]:  # 如插件参数不正确则使用对话模型判断
        i_say_show_user = (
            f"接下来将判断适合的图表类型,如连续3次判断失败将会使用流程图进行绘制"
        )
        gpt_say = "[Local Message] 收到。"  # 用户提示
        chatbot.append([i_say_show_user, gpt_say])
        yield from update_ui(chatbot=chatbot, history=[])  # 更新UI
        i_say = SELECT_PROMPT.format(subject=results_txt)
        i_say_show_user = f'请判断适合使用的流程图类型,其中数字对应关系为:1-流程图,2-序列图,3-类图,4-饼图,5-甘特图,6-状态图,7-实体关系图,8-象限提示图。由于不管提供文本是什么,模型大概率认为"思维导图"最合适,因此思维导图仅能通过参数调用。'
        for i in range(3):
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs,
                chatbot=chatbot,
                history=[],
                sys_prompt="",
            )
            if gpt_say in [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
            ]:  # 判断返回是否正确
                break
        if gpt_say not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            gpt_say = "1"
    ############################## <第 3 步，根据选择的图表类型绘制图表> ##################################
    if gpt_say == "1":
        i_say = PROMPT_1.format(subject=results_txt)
    elif gpt_say == "2":
        i_say = PROMPT_2.format(subject=results_txt)
    elif gpt_say == "3":
        i_say = PROMPT_3.format(subject=results_txt)
    elif gpt_say == "4":
        i_say = PROMPT_4.format(subject=results_txt)
    elif gpt_say == "5":
        i_say = PROMPT_5.format(subject=results_txt)
    elif gpt_say == "6":
        i_say = PROMPT_6.format(subject=results_txt)
    elif gpt_say == "7":
        i_say = PROMPT_7.replace("{subject}", results_txt)  # 由于实体关系图用到了{}符号
    elif gpt_say == "8":
        i_say = PROMPT_8.format(subject=results_txt)
    elif gpt_say == "9":
        i_say = PROMPT_9.format(subject=results_txt)
    i_say_show_user = f"请根据判断结果绘制相应的图表。如需绘制思维导图请使用参数调用,同时过大的图表可能需要复制到在线编辑器中进行渲染。"
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say,
        inputs_show_user=i_say_show_user,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        history=[],
        sys_prompt="",
    )
    history.append(gpt_say)
    yield from update_ui(chatbot=chatbot, history=history)