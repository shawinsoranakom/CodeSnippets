def Audio_Summary(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, WEB_PORT):
    import glob, os

    # 基本信息：功能、贡献者
    chatbot.append([
        "函数插件功能？",
        "Audio_Summary内容，函数插件贡献者: dalvqw & BinaryHusky"])
    yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面

    try:
        from moviepy.editor import AudioFileClip
    except:
        report_exception(chatbot, history,
                         a=f"解析项目: {txt}",
                         b=f"导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade moviepy```。")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    # 清空历史，以免输入溢出
    history = []

    # 检测输入参数，如没有给定输入参数，直接退出
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空空如也的输入栏'
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到本地项目或无权访问: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    # 搜索需要处理的文件清单
    extensions = ['.mp4', '.m4a', '.wav', '.mpga', '.mpeg', '.mp3', '.avi', '.mkv', '.flac', '.aac']

    if txt.endswith(tuple(extensions)):
        file_manifest = [txt]
    else:
        file_manifest = []
        for extension in extensions:
            file_manifest.extend(glob.glob(f'{project_folder}/**/*{extension}', recursive=True))

    # 如果没找到任何文件
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到任何音频或视频文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
        return

    # 开始正式执行任务
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    parse_prompt = plugin_kwargs.get("advanced_arg", '将音频解析为简体中文')
    yield from AnalyAudio(parse_prompt, file_manifest, llm_kwargs, chatbot, history)

    yield from update_ui(chatbot=chatbot, history=history)