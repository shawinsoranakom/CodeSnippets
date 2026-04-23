def 多文件翻译(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en'):
    from crazy_functions.crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency

    #  <-------- 读取Markdown文件，删除其中的所有注释 ---------->
    pfg = PaperFileGroup()

    for index, fp in enumerate(file_manifest):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
            # 记录删除注释后的文本
            pfg.file_paths.append(fp)
            pfg.file_contents.append(file_content)

    #  <-------- 拆分过长的Markdown文件 ---------->
    pfg.run_file_split(max_token_limit=1024)
    n_split = len(pfg.sp_file_contents)

    #  <-------- 多线程翻译开始 ---------->
    if language == 'en->zh':
        inputs_array = ["This is a Markdown file, translate it into Chinese, do NOT modify any existing Markdown commands, do NOT use code wrapper (```), ONLY answer me with translated results:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻译 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." + plugin_kwargs.get("additional_prompt", "") for _ in range(n_split)]
    elif language == 'zh->en':
        inputs_array = [f"This is a Markdown file, translate it into English, do NOT modify any existing Markdown commands, do NOT use code wrapper (```), ONLY answer me with translated results:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻译 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." + plugin_kwargs.get("additional_prompt", "") for _ in range(n_split)]
    else:
        inputs_array = [f"This is a Markdown file, translate it into {language}, do NOT modify any existing Markdown commands, do NOT use code wrapper (```), ONLY answer me with translated results:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻译 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." + plugin_kwargs.get("additional_prompt", "") for _ in range(n_split)]

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
    try:
        pfg.sp_file_result = []
        for i_say, gpt_say in zip(gpt_response_collection[0::2], gpt_response_collection[1::2]):
            pfg.sp_file_result.append(gpt_say)
        pfg.merge_result()
        output_file_arr = pfg.write_result(language)
        for output_file in output_file_arr:
            promote_file_to_downloadzone(output_file, chatbot=chatbot)
            if 'markdown_expected_output_path' in plugin_kwargs:
                expected_f_name = plugin_kwargs['markdown_expected_output_path']
                shutil.copyfile(output_file, expected_f_name)
    except:
        logger.error(trimmed_format_exc())

    #  <-------- 整理结果，退出 ---------->
    create_report_file_name = gen_time_str() + f"-chatgpt.md"
    res = write_history_to_file(gpt_response_collection, file_basename=create_report_file_name)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    history = gpt_response_collection
    chatbot.append((f"{fp}完成了吗？", res))
    yield from update_ui(chatbot=chatbot, history=history)