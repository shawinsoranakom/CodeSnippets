def 批量文件询问(txt: str, llm_kwargs: Dict, plugin_kwargs: Dict, chatbot: List,
                 history: List, system_prompt: str, user_request: str):
    """主函数 - 优化版本"""
    # 初始化
    import glob
    import re
    from crazy_functions.rag_fns.rag_file_support import supports_format
    from toolbox import report_exception
    query = plugin_kwargs.get("advanced_arg")
    summarizer = BatchDocumentSummarizer(llm_kwargs, query, chatbot, history, system_prompt)
    chatbot.append(["函数插件功能", f"作者：lbykkkk，批量总结文件。支持格式: {', '.join(supports_format)}等其他文本格式文件，如果长时间卡在文件处理过程，请查看处理进度，然后删除所有处于“pending”状态的文件，然后重新上传处理。"])
    yield from update_ui(chatbot=chatbot, history=history)

    # 验证输入路径
    if not os.path.exists(txt):
        report_exception(chatbot, history, a=f"解析项目: {txt}", b=f"找不到项目或无权访问: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)
        return

    # 获取文件列表
    project_folder = txt
    user_name = chatbot.get_user()
    validate_path_safety(project_folder, user_name)
    extract_folder = next((d for d in glob.glob(f'{project_folder}/*')
                           if os.path.isdir(d) and d.endswith('.extract')), project_folder)
    exclude_patterns = r'/[^/]+\.(zip|rar|7z|tar|gz)$'
    file_manifest = [f for f in glob.glob(f'{extract_folder}/**', recursive=True)
                     if os.path.isfile(f) and not re.search(exclude_patterns, f)]

    if not file_manifest:
        report_exception(chatbot, history, a=f"解析项目: {txt}", b="未找到支持的文件类型")
        yield from update_ui(chatbot=chatbot, history=history)
        return

    # 处理所有文件并生成总结
    final_summary = yield from summarizer.process_files(project_folder, file_manifest)
    yield from update_ui(chatbot=chatbot, history=history)

    # 保存结果
    summarizer.save_results(final_summary)
    yield from update_ui(chatbot=chatbot, history=history)