def 多文件翻译(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en'):
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

    #  <-------- 抽取摘要 ---------->
    # if language == 'en':
    #     abs_extract_inputs = f"Please write an abstract for this paper"

    # # 单线，获取文章meta信息
    # paper_meta_info = yield from request_gpt_model_in_new_thread_with_ui_alive(
    #     inputs=abs_extract_inputs,
    #     inputs_show_user=f"正在抽取摘要信息。",
    #     llm_kwargs=llm_kwargs,
    #     chatbot=chatbot, history=[],
    #     sys_prompt="Your job is to collect information from materials。",
    # )

    #  <-------- 多线程润色开始 ---------->
    if language == 'en->zh':
        inputs_array = ["Below is a section from an English academic paper, translate it into Chinese, do not modify any latex command such as \section, \cite and equations:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻译 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." for _ in range(n_split)]
    elif language == 'zh->en':
        inputs_array = [f"Below is a section from a Chinese academic paper, translate it into English, do not modify any latex command such as \section, \cite and equations:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻译 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." for _ in range(n_split)]

    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        history_array=[[""] for _ in range(n_split)],
        sys_prompt_array=sys_prompt_array,
        # max_workers=5,  # OpenAI所允许的最大并行过载
        scroller_max_len = 80
    )

    #  <-------- 整理结果，退出 ---------->
    create_report_file_name = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + f"-chatgpt.polish.md"
    res = write_history_to_file(gpt_response_collection, create_report_file_name)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    history = gpt_response_collection
    chatbot.append((f"{fp}完成了吗？", res))
    yield from update_ui(chatbot=chatbot, history=history)