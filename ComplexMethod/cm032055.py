def Mermaid_Figure_Gen(
    txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, web_port
):
    """
    txt             输入栏用户输入的文本，例如需要翻译的一段话，再例如一个包含了待处理文件的路径
    llm_kwargs      gpt模型参数，如温度和top_p等，一般原样传递下去就行
    plugin_kwargs   插件模型的参数，用于灵活调整复杂功能的各种参数
    chatbot         聊天显示框的句柄，用于显示给用户
    history         聊天历史，前情提要
    system_prompt   给gpt的静默提醒
    web_port        当前软件运行的端口号
    """
    import os

    # 基本信息：功能、贡献者
    chatbot.append(
        [
            "函数插件功能？",
            "根据当前聊天历史或指定的路径文件(文件内容优先)绘制多种mermaid图表，将会由对话模型首先判断适合的图表类型，随后绘制图表。\
        \n您也可以使用插件参数指定绘制的图表类型,函数插件贡献者: Menghuan1918",
        ]
    )
    yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面

    if os.path.exists(txt):  # 如输入区无内容则直接解析历史记录
        from crazy_functions.pdf_fns.parse_word import extract_text_from_files

        file_exist, final_result, page_one, file_manifest, exception = (
            extract_text_from_files(txt, chatbot, history)
        )
    else:
        file_exist = False
        exception = ""
        file_manifest = []

    if exception != "":
        if exception == "word":
            report_exception(
                chatbot,
                history,
                a=f"解析项目: {txt}",
                b=f"找到了.doc文件，但是该文件格式不被支持，请先转化为.docx格式。",
            )

        elif exception == "pdf":
            report_exception(
                chatbot,
                history,
                a=f"解析项目: {txt}",
                b=f"导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade pymupdf```。",
            )

        elif exception == "word_pip":
            report_exception(
                chatbot,
                history,
                a=f"解析项目: {txt}",
                b=f"导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade python-docx pywin32```。",
            )

        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面

    else:
        if not file_exist:
            history.append(txt)  # 如输入区不是文件则将输入区内容加入历史记录
            i_say_show_user = f"首先你从历史记录中提取摘要。"
            gpt_say = "[Local Message] 收到。"  # 用户提示
            chatbot.append([i_say_show_user, gpt_say])
            yield from update_ui(chatbot=chatbot, history=history)  # 更新UI
            yield from 解析历史输入(
                history, llm_kwargs, file_manifest, chatbot, plugin_kwargs
            )
        else:
            file_num = len(file_manifest)
            for i in range(file_num):  # 依次处理文件
                i_say_show_user = f"[{i+1}/{file_num}]处理文件{file_manifest[i]}"
                gpt_say = "[Local Message] 收到。"  # 用户提示
                chatbot.append([i_say_show_user, gpt_say])
                yield from update_ui(chatbot=chatbot, history=history)  # 更新UI
                history = []  # 如输入区内容为文件则清空历史记录
                history.append(final_result[i])
                yield from 解析历史输入(
                    history, llm_kwargs, file_manifest, chatbot, plugin_kwargs
                )