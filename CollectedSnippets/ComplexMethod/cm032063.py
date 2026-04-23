def Word_Summary(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    import glob, os

    # 基本信息：功能、贡献者
    chatbot.append([
        "函数插件功能？",
        "批量Word_Summary。函数插件贡献者: JasonGuo1。注意, 如果是.doc文件, 请先转化为.docx格式。"])
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面

    # 尝试导入依赖，如果缺少依赖，则给出安装建议
    try:
        from docx import Document
    except:
        report_exception(chatbot, history,
                         a=f"解析项目: {txt}",
                         b=f"导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade python-docx pywin32```。")
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return

    # 清空历史，以免输入溢出
    history = []

    # 检测输入参数，如没有给定输入参数，直接退出
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空空如也的输入栏'
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到本地项目或无权访问: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return

    # 搜索需要处理的文件清单
    if txt.endswith('.docx') or txt.endswith('.doc'):
        file_manifest = [txt]
    else:
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.docx', recursive=True)] + \
                        [f for f in glob.glob(f'{project_folder}/**/*.doc', recursive=True)]

    # 如果没找到任何文件
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到任何.docx或doc文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return

    # 开始正式执行任务
    yield from 解析docx(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)