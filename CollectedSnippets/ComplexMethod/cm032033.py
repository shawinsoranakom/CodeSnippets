def Latex翻译中文并重新编译PDF(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # <-------------- information about this plugin ------------->
    chatbot.append([
        "函数插件功能？",
        "对整个Latex项目进行翻译, 生成中文PDF。函数插件贡献者: Binary-Husky。注意事项: 此插件Windows支持最佳，Linux下必须使用Docker安装，详见项目主README.md。目前对机器学习类文献转化效果最好，其他类型文献转化效果未知。"])
    yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面

    # <-------------- more requirements ------------->
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    more_req = plugin_kwargs.get("advanced_arg", "")

    no_cache = ("--no-cache" in more_req)
    if no_cache: more_req = more_req.replace("--no-cache", "").strip()

    allow_gptac_cloud_io = ("--allow-cloudio" in more_req)  # 从云端下载翻译结果，以及上传翻译结果到云端
    if allow_gptac_cloud_io: more_req = more_req.replace("--allow-cloudio", "").strip()

    allow_cache = not no_cache
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
    try:
        txt, arxiv_id = yield from arxiv_download(chatbot, history, txt, allow_cache)
    except tarfile.ReadError as e:
        yield from update_ui_latest_msg(
            "无法自动下载该论文的Latex源码，请前往arxiv打开此论文下载页面，点other Formats，然后download source手动下载latex源码包。接下来调用本地Latex翻译插件即可。",
            chatbot=chatbot, history=history)
        return

    if txt.endswith('.pdf'):
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"发现已经存在翻译好的PDF文档")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    # #################################################################
    if allow_gptac_cloud_io and arxiv_id:
        # 访问 GPTAC学术云，查询云端是否存在该论文的翻译版本
        from crazy_functions.latex_fns.latex_actions import check_gptac_cloud
        success, downloaded = check_gptac_cloud(arxiv_id, chatbot)
        if success:
            chatbot.append([
                f"检测到GPTAC云端存在翻译版本, 如果不满意翻译结果, 请禁用云端分享, 然后重新执行。",
                None
            ])
            yield from update_ui(chatbot=chatbot, history=history)
            return
    #################################################################

    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空空如也的输入栏'
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到本地项目或无法处理: {txt}")
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
    project_folder = move_project(project_folder, arxiv_id)

    # <-------------- if merge_translate_zh is already generated, skip gpt req ------------->
    if not os.path.exists(project_folder + '/merge_translate_zh.tex'):
        yield from Latex精细分解与转化(file_manifest, project_folder, llm_kwargs, plugin_kwargs,
                                       chatbot, history, system_prompt, mode='translate_zh',
                                       switch_prompt=_switch_prompt_)

    # <-------------- compile PDF ------------->
    success = yield from 编译Latex(chatbot, history, main_file_original='merge',
                                   main_file_modified='merge_translate_zh', mode='translate_zh',
                                   work_folder_original=project_folder, work_folder_modified=project_folder,
                                   work_folder=project_folder)

    # <-------------- zip PDF ------------->
    zip_res = zip_result(project_folder)
    if success:
        if allow_gptac_cloud_io and arxiv_id:
            # 如果用户允许，我们将翻译好的arxiv论文PDF上传到GPTAC学术云
            from crazy_functions.latex_fns.latex_actions import upload_to_gptac_cloud_if_user_allow
            threading.Thread(target=upload_to_gptac_cloud_if_user_allow,
                args=(chatbot, arxiv_id), daemon=True).start()

        chatbot.append((f"成功啦", '请查收结果（压缩包）...'))
        yield from update_ui(chatbot=chatbot, history=history)
        time.sleep(1)  # 刷新界面
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

    else:
        chatbot.append((f"失败了",
                        '虽然PDF生成失败了, 但请查收结果（压缩包）, 内含已经翻译的Tex文档, 您可以到Github Issue区, 用该压缩包进行反馈。如系统是Linux，请检查系统字体（见Github wiki） ...'))
        yield from update_ui(chatbot=chatbot, history=history)
        time.sleep(1)  # 刷新界面
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

    # <-------------- we are done ------------->
    return success