def Latex英文纠错加PDF对比(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # <-------------- information about this plugin ------------->
    chatbot.append(["函数插件功能？",
                    "对整个Latex项目进行纠错, 用latex编译为PDF对修正处做高亮。函数插件贡献者: Binary-Husky。注意事项: 目前对机器学习类文献转化效果最好，其他类型文献转化效果未知。仅在Windows系统进行了测试，其他操作系统表现未知。"])
    yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面

    # <-------------- more requirements ------------->
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    more_req = plugin_kwargs.get("advanced_arg", "")
    _switch_prompt_ = partial(switch_prompt, more_requirement=more_req)

    # <-------------- check deps ------------->
    try:
        import glob, os, time, subprocess
        subprocess.Popen(['pdflatex', '-version'])
        from .latex_fns.latex_actions import Latex精细分解与转化, 编译Latex
    except Exception as e:
        chatbot.append([f"解析项目: {txt}",
                        f"尝试执行Latex指令失败。Latex没有安装, 或者不在环境变量PATH中。安装方法https://tug.org/texlive/。报错信息\n\n```\n\n{trimmed_format_exc()}\n\n```\n\n"])
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    # <-------------- clear history and read input ------------->
    history = []
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空空如也的输入栏'
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到本地项目或无权访问: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到任何.tex文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    # <-------------- if is a zip/tar file ------------->
    project_folder = descend_to_extracted_folder_if_exist(project_folder)

    # <-------------- move latex project away from temp folder ------------->
    from shared_utils.fastapi_server import validate_path_safety
    validate_path_safety(project_folder, chatbot.get_user())
    project_folder = move_project(project_folder, arxiv_id=None)

    # <-------------- if merge_translate_zh is already generated, skip gpt req ------------->
    if not os.path.exists(project_folder + '/merge_proofread_en.tex'):
        yield from Latex精细分解与转化(file_manifest, project_folder, llm_kwargs, plugin_kwargs,
                                       chatbot, history, system_prompt, mode='proofread_en',
                                       switch_prompt=_switch_prompt_)

    # <-------------- compile PDF ------------->
    success = yield from 编译Latex(chatbot, history, main_file_original='merge',
                                   main_file_modified='merge_proofread_en',
                                   work_folder_original=project_folder, work_folder_modified=project_folder,
                                   work_folder=project_folder)

    # <-------------- zip PDF ------------->
    zip_res = zip_result(project_folder)
    if success:
        chatbot.append((f"成功啦", '请查收结果（压缩包）...'))
        yield from update_ui(chatbot=chatbot, history=history);
        time.sleep(1)  # 刷新界面
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)
    else:
        chatbot.append((f"失败了",
                        '虽然PDF生成失败了, 但请查收结果（压缩包）, 内含已经翻译的Tex文档, 也是可读的, 您可以到Github Issue区, 用该压缩包+Conversation_To_File进行反馈 ...'))
        yield from update_ui(chatbot=chatbot, history=history);
        time.sleep(1)  # 刷新界面
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

    # <-------------- we are done ------------->
    return success