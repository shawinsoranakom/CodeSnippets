def 多文件润色(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en', mode='polish'):
    import time, os, re
    from crazy_functions.crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency


    #  <-------- 读取Latex文件，删除其中的所有注释 ---------->
    pfg = PaperFileGroup()

    for index, fp in enumerate(file_manifest):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
            # 定义注释的正则表达式
            comment_pattern = r'(?<!\\)%.*'
            # 使用正则表达式查找注释，并替换为空字符串
            clean_tex_content = re.sub(comment_pattern, '', file_content)
            # 记录删除注释后的文本
            pfg.file_paths.append(fp)
            pfg.file_contents.append(clean_tex_content)

    #  <-------- 拆分过长的latex文件 ---------->
    pfg.run_file_split(max_token_limit=1024)
    n_split = len(pfg.sp_file_contents)


    #  <-------- 多线程润色开始 ---------->
    if language == 'en':
        if mode == 'polish':
            inputs_array = [r"Below is a section from an academic paper, polish this section to meet the academic standard, " +
                            r"improve the grammar, clarity and overall readability, do not modify any latex command such as \section, \cite and equations:" +
                            f"\n\n{frag}" for frag in pfg.sp_file_contents]
        else:
            inputs_array = [r"Below is a section from an academic paper, proofread this section." +
                            r"Do not modify any latex command such as \section, \cite, \begin, \item and equations. " +
                            r"Answer me only with the revised text:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"Polish {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper writer." for _ in range(n_split)]
    elif language == 'zh':
        if mode == 'polish':
            inputs_array = [r"以下是一篇学术论文中的一段内容，请将此部分润色以满足学术标准，提高语法、清晰度和整体可读性，不要修改任何LaTeX命令，例如\section，\cite和方程式：" +
                            f"\n\n{frag}" for frag in pfg.sp_file_contents]
        else:
            inputs_array = [r"以下是一篇学术论文中的一段内容，请对这部分内容进行语法矫正。不要修改任何LaTeX命令，例如\section，\cite和方程式：" +
                            f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"润色 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array=["你是一位专业的中文学术论文作家。" for _ in range(n_split)]


    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        history_array=[[""] for _ in range(n_split)],
        sys_prompt_array=sys_prompt_array,
        # max_workers=5,  # 并行任务数量限制，最多同时执行5个，其他的排队等待
        scroller_max_len = 80
    )

    #  <-------- 文本碎片重组为完整的tex文件，整理结果为压缩包 ---------->
    try:
        pfg.sp_file_result = []
        for i_say, gpt_say in zip(gpt_response_collection[0::2], gpt_response_collection[1::2]):
            pfg.sp_file_result.append(gpt_say)
        pfg.merge_result()
        pfg.write_result()
        pfg.zip_result()
    except:
        logger.error(trimmed_format_exc())

    #  <-------- 整理结果，退出 ---------->
    create_report_file_name = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + f"-chatgpt.polish.md"
    res = write_history_to_file(gpt_response_collection, file_basename=create_report_file_name)
    promote_file_to_downloadzone(res, chatbot=chatbot)

    history = gpt_response_collection
    chatbot.append((f"{fp}完成了吗？", res))
    yield from update_ui(chatbot=chatbot, history=history)