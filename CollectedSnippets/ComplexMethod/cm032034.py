def PDF翻译中文并重新编译PDF(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, web_port):
    # <-------------- information about this plugin ------------->
    chatbot.append([
        "函数插件功能？",
        "将PDF转换为Latex项目，翻译为中文后重新编译为PDF。函数插件贡献者: Marroh。注意事项: 此插件Windows支持最佳，Linux下必须使用Docker安装，详见项目主README.md。目前对机器学习类文献转化效果最好，其他类型文献转化效果未知。"])
    yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面

    # <-------------- more requirements ------------->
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    more_req = plugin_kwargs.get("advanced_arg", "")
    no_cache = more_req.startswith("--no-cache")
    if no_cache: more_req.lstrip("--no-cache")
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
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空空如也的输入栏'
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到本地项目或无法处理: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.pdf', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到任何.pdf文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return
    if len(file_manifest) != 1:
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"不支持同时处理多个pdf文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    if plugin_kwargs.get("method", "") == 'MATHPIX':
        app_id, app_key = get_conf('MATHPIX_APPID', 'MATHPIX_APPKEY')
        if len(app_id) == 0 or len(app_key) == 0:
            report_exception(chatbot, history, a="缺失 MATHPIX_APPID 和 MATHPIX_APPKEY。", b=f"请配置 MATHPIX_APPID 和 MATHPIX_APPKEY")
            yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
            return
    if plugin_kwargs.get("method", "") == 'DOC2X':
        app_id, app_key = "", ""
        DOC2X_API_KEY = get_conf('DOC2X_API_KEY')
        if len(DOC2X_API_KEY) == 0:
            report_exception(chatbot, history, a="缺失 DOC2X_API_KEY。", b=f"请配置 DOC2X_API_KEY")
            yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
            return

    hash_tag = map_file_to_sha256(file_manifest[0])

    # # <-------------- check repeated pdf ------------->
    # chatbot.append([f"检查PDF是否被重复上传", "正在检查..."])
    # yield from update_ui(chatbot=chatbot, history=history)
    # repeat, project_folder = check_repeat_upload(file_manifest[0], hash_tag)

    # if repeat:
    #     yield from update_ui_latest_msg(f"发现重复上传，请查收结果（压缩包）...", chatbot=chatbot, history=history)
    #     try:
    #         translate_pdf = [f for f in glob.glob(f'{project_folder}/**/merge_translate_zh.pdf', recursive=True)][0]
    #         promote_file_to_downloadzone(translate_pdf, rename_file=None, chatbot=chatbot)
    #         comparison_pdf = [f for f in glob.glob(f'{project_folder}/**/comparison.pdf', recursive=True)][0]
    #         promote_file_to_downloadzone(comparison_pdf, rename_file=None, chatbot=chatbot)
    #         zip_res = zip_result(project_folder)
    #         promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)
    #         return
    #     except:
    #         report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"发现重复上传，但是无法找到相关文件")
    #         yield from update_ui(chatbot=chatbot, history=history)
    # else:
    #     yield from update_ui_latest_msg(f"未发现重复上传", chatbot=chatbot, history=history)

    # <-------------- convert pdf into tex ------------->
    chatbot.append([f"解析项目: {txt}", "正在将PDF转换为tex项目，请耐心等待..."])
    yield from update_ui(chatbot=chatbot, history=history)
    project_folder = pdf2tex_project(file_manifest[0], plugin_kwargs)
    if project_folder is None:
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"PDF转换为tex项目失败")
        yield from update_ui(chatbot=chatbot, history=history)
        return False

    # <-------------- translate latex file into Chinese ------------->
    yield from update_ui_latest_msg("正在tex项目将翻译为中文...", chatbot=chatbot, history=history)
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
    project_folder = move_project(project_folder)

    # <-------------- set a hash tag for repeat-checking ------------->
    with open(pj(project_folder, hash_tag + '.tag'), 'w', encoding='utf8') as f:
        f.write(hash_tag)
        f.close()


    # <-------------- if merge_translate_zh is already generated, skip gpt req ------------->
    if not os.path.exists(project_folder + '/merge_translate_zh.tex'):
        yield from Latex精细分解与转化(file_manifest, project_folder, llm_kwargs, plugin_kwargs,
                                    chatbot, history, system_prompt, mode='translate_zh',
                                    switch_prompt=_switch_prompt_)

    # <-------------- compile PDF ------------->
    yield from update_ui_latest_msg("正在将翻译好的项目tex项目编译为PDF...", chatbot=chatbot, history=history)
    success = yield from 编译Latex(chatbot, history, main_file_original='merge',
                                main_file_modified='merge_translate_zh', mode='translate_zh',
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
                        '虽然PDF生成失败了, 但请查收结果（压缩包）, 内含已经翻译的Tex文档, 您可以到Github Issue区, 用该压缩包进行反馈。如系统是Linux，请检查系统字体（见Github wiki） ...'))
        yield from update_ui(chatbot=chatbot, history=history);
        time.sleep(1)  # 刷新界面
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

    # <-------------- we are done ------------->
    return success