def 批量翻译PDF文档(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):

    disable_auto_promotion(chatbot)
    # 基本信息：功能、贡献者
    chatbot.append([
        "函数插件功能？",
        "批量翻译PDF文档。函数插件贡献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面

    # 清空历史，以免输入溢出
    history = []

    from crazy_functions.crazy_utils import get_files_from_everything
    success, file_manifest, project_folder = get_files_from_everything(txt, type='.pdf')
    if len(file_manifest) > 0:
        # 尝试导入依赖，如果缺少依赖，则给出安装建议
        try:
            import nougat
            import tiktoken
        except:
            report_exception(chatbot, history,
                             a=f"解析项目: {txt}",
                             b=f"导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade nougat-ocr tiktoken```。")
            yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
            return
    success_mmd, file_manifest_mmd, _ = get_files_from_everything(txt, type='.mmd')
    success = success or success_mmd
    file_manifest += file_manifest_mmd
    chatbot.append(["文件列表：", ", ".join([e.split('/')[-1] for e in file_manifest])]);
    yield from update_ui(      chatbot=chatbot, history=history)
    # 检测输入参数，如没有给定输入参数，直接退出
    if not success:
        if txt == "": txt = '空空如也的输入栏'

    # 如果没找到任何文件
    if len(file_manifest) == 0:
        report_exception(chatbot, history,
                         a=f"解析项目: {txt}", b=f"找不到任何.pdf拓展名的文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return

    # 开始正式执行任务
    yield from 解析PDF_基于NOUGAT(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)